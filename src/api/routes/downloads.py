"""Download queue endpoints.

``POST`` enqueues work, ``GET`` polls progress, ``DELETE`` cancels. Progress is
polled rather than pushed: one worker process, a handful of concurrent
downloads, and a browser that already wants a refresh loop.
"""
from __future__ import annotations

import asyncio
from typing import Any, cast

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.api.deps import get_db
from src.schemas.spotify_types import TrackDict
from src.services.download_queue import get_queue

router = APIRouter(prefix="/api/downloads", tags=["downloads"])


class DownloadRequest(BaseModel):
    """Select tracks to download, either explicitly or from a playlist."""

    track_ids: list[str] = Field(default_factory=list)
    playlist_id: str | None = None
    include_downloaded: bool = False


def _resolve_tracks(request: DownloadRequest) -> list[TrackDict]:
    """Expand a request into the concrete tracks the queue should process."""
    db = get_db()

    rows: list[dict[str, Any]]
    if request.playlist_id:
        rows = [dict(row) for row in db.get_playlist_tracks(request.playlist_id)]
        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"playlist {request.playlist_id} has no tracks",
            )
    elif request.track_ids:
        wanted = set(request.track_ids)
        rows = [dict(track) for track in db.get_all_unique_tracks()
                if track["id"] in wanted]
        missing = wanted - {str(row["id"]) for row in rows}
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"unknown track ids: {sorted(missing)}",
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="provide either track_ids or playlist_id",
        )

    tracks: list[TrackDict] = []
    for row in rows:
        if not request.include_downloaded and row.get("downloaded"):
            continue
        row.pop("position", None)  # playlist rows carry ordering; track rows don't
        tracks.append(cast(TrackDict, row))

    return tracks


@router.post("", status_code=202)
async def enqueue_downloads(request: DownloadRequest) -> dict[str, Any]:
    """Queue tracks for download and return the created jobs."""
    # Database access is blocking sqlite, so keep it off the event loop.
    tracks = await asyncio.to_thread(_resolve_tracks, request)

    if not tracks:
        return {"enqueued": 0, "jobs": [], "detail": "nothing to download"}

    queue = get_queue()
    jobs = [queue.enqueue(track) for track in tracks]

    return {"enqueued": len(jobs), "jobs": [job.as_dict() for job in jobs]}


@router.get("")
async def list_downloads() -> dict[str, Any]:
    """All jobs in this process, newest first, with state counts."""
    queue = get_queue()
    return {"items": queue.snapshot(), "counts": queue.counts()}


@router.get("/{job_id}")
async def get_download(job_id: str) -> dict[str, Any]:
    """Progress for a single job."""
    job = get_queue().get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"no job with id {job_id}")
    return job.as_dict()


@router.delete("/{job_id}")
async def cancel_download(job_id: str) -> dict[str, Any]:
    """Cancel a queued job.

    Running jobs cannot be interrupted: yt-dlp is mid-call on a worker thread.
    The response says so rather than pretending the download stopped.
    """
    queue = get_queue()
    job = queue.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"no job with id {job_id}")

    cancelled = queue.cancel(job_id)
    detail = None if cancelled else "a running download cannot be interrupted"

    return {"cancelled": cancelled, "detail": detail, "job": job.as_dict()}
