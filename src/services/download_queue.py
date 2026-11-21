"""In-process download job queue for the yt-dlp backend.

yt-dlp is blocking, so each download runs on a worker thread while the event
loop stays free to answer API requests. Job state lives in memory: this is
progress reporting for a single-user local app, not durable job storage. If the
process dies mid-download the job is simply gone; ``tracks.downloaded`` in the
database remains the source of truth about what actually landed on disk.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from src.download_tracks import download_single_track
from src.schemas.spotify_types import TrackDict

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class JobState(StrEnum):
    """Lifecycle of a single download job."""

    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class DownloadJob:
    """A single track download and its current progress."""

    id: str
    track_id: str
    name: str
    artists: list[str]
    state: JobState = JobState.QUEUED
    progress: float = 0.0
    stage: str = "queued"
    file_path: str | None = None
    error: str | None = None
    created_at: str = field(default_factory=_now)
    finished_at: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "track_id": self.track_id,
            "name": self.name,
            "artists": self.artists,
            "state": str(self.state),
            "progress": round(self.progress, 4),
            "stage": self.stage,
            "file_path": self.file_path,
            "error": self.error,
            "created_at": self.created_at,
            "finished_at": self.finished_at,
        }


class DownloadQueue:
    """Serial download queue backed by a single asyncio worker.

    Downloads run one at a time on purpose: yt-dlp is I/O bound against a single
    upstream service, and hammering it in parallel mostly produces failures.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, DownloadJob] = {}
        self._tracks: dict[str, TrackDict] = {}
        self._pending: asyncio.Queue[str] = asyncio.Queue()
        self._worker: asyncio.Task[None] | None = None

    # -- public API ---------------------------------------------------------

    def enqueue(self, track: TrackDict) -> DownloadJob:
        """Queue a track and return its job record.

        Must be called from the event loop thread: starting the worker task
        requires a running loop.
        """
        job = DownloadJob(
            id=uuid4().hex,
            track_id=track["id"],
            name=track["name"],
            artists=list(track["artists"]),
        )
        self._jobs[job.id] = job
        self._tracks[job.id] = track
        self._pending.put_nowait(job.id)
        self._ensure_worker()
        return job

    def get(self, job_id: str) -> DownloadJob | None:
        return self._jobs.get(job_id)

    def snapshot(self) -> list[dict[str, object]]:
        """All jobs, newest first."""
        jobs = sorted(
            self._jobs.values(),
            key=lambda job: job.created_at,
            reverse=True,
        )
        return [job.as_dict() for job in jobs]

    def counts(self) -> dict[str, int]:
        counts = {state.value: 0 for state in JobState}
        for job in self._jobs.values():
            counts[str(job.state)] += 1
        return counts

    def cancel(self, job_id: str) -> bool:
        """Cancel a queued job. Returns False if it was already running."""
        job = self._jobs.get(job_id)
        if job is None:
            return False

        if job.state is not JobState.QUEUED:
            # The download is inside a blocking yt-dlp call on a worker thread.
            # There is no safe way to interrupt it, so report that honestly
            # instead of marking it cancelled while it keeps writing to disk.
            return False

        job.state = JobState.CANCELLED
        job.stage = "cancelled"
        job.finished_at = _now()
        return True

    # -- internals ----------------------------------------------------------

    def _ensure_worker(self) -> None:
        if self._worker is None or self._worker.done():
            self._worker = asyncio.create_task(
                self._worker_loop(), name="download-worker"
            )

    async def _worker_loop(self) -> None:
        while True:
            job_id = await self._pending.get()
            try:
                job = self._jobs.get(job_id)
                if job is None or job.state is not JobState.QUEUED:
                    continue
                await self._run(job)
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 - one bad job must not kill the worker
                logger.exception("download job %s crashed", job_id)
            finally:
                self._pending.task_done()

    async def _run(self, job: DownloadJob) -> None:
        track = self._tracks.get(job.id)
        if track is None:
            job.state = JobState.FAILED
            job.error = "track data missing"
            job.stage = "failed"
            job.finished_at = _now()
            return

        job.state = JobState.RUNNING
        job.stage = "starting"

        def on_progress(fraction: float, stage: str) -> None:
            # Called from the yt-dlp worker thread. Assigning a float/str is
            # atomic under the GIL, which is all this needs.
            job.progress = max(0.0, min(1.0, fraction))
            job.stage = stage

        try:
            file_path = await asyncio.to_thread(
                download_single_track, track, on_progress
            )
        except Exception as exc:  # noqa: BLE001 - surfaced through the API
            logger.exception("download failed for track %s", job.track_id)
            job.state = JobState.FAILED
            job.error = f"{type(exc).__name__}: {exc}"
            job.stage = "failed"
            job.finished_at = _now()
            return

        if file_path is None:
            job.state = JobState.FAILED
            job.error = "download failed (no file produced)"
            job.stage = "failed"
        else:
            job.state = JobState.DONE
            job.stage = "done"
            job.progress = 1.0
            job.file_path = file_path

        job.finished_at = _now()


_queue: DownloadQueue | None = None


def get_queue() -> DownloadQueue:
    """Process-wide download queue.

    Must be called from the event loop thread so that ``enqueue`` can start the
    worker task.
    """
    global _queue
    if _queue is None:
        _queue = DownloadQueue()
    return _queue
