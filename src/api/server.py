import io
import os
import queue
import sys
import threading
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from database.db_manager import Database

app = FastAPI(
    title="Spotipyt",
    description="Local music library server",
    version="1.0.0"
)

# Project root = two levels up from this file (src/api/server.py → project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ── Background job state ──────────────────────────────────────────────────────

_job_lock = threading.Lock()
_job_state: dict = {"status": "idle", "type": None, "logs": []}
_log_queue: queue.Queue = queue.Queue()


class _QueueWriter(io.TextIOBase):
    """Redirects print() output into the log queue during a job."""
    def write(self, s: str) -> int:
        if s and s != "\n":
            _log_queue.put(s.rstrip())
        return len(s)
    def flush(self): pass


def _run_job(job_type: str, fn):
    with _job_lock:
        _job_state["status"] = "running"
        _job_state["type"] = job_type
        _job_state["logs"] = []
    _log_queue.put(f"[{job_type}] starting…")
    writer = _QueueWriter()
    try:
        with redirect_stdout(writer), redirect_stderr(writer):
            fn()
        _log_queue.put(f"[{job_type}] done ✓")
        with _job_lock:
            _job_state["status"] = "done"
    except Exception as exc:
        _log_queue.put(f"[{job_type}] error: {exc}")
        with _job_lock:
            _job_state["status"] = "error"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_db_path = os.environ.get("DB_PATH") or str(_PROJECT_ROOT / "music.db")
db = Database(_db_path)

_downloads_dir = Path(os.environ.get("DOWNLOADS_DIR") or str(_PROJECT_ROOT / "downloads")).resolve()
_covers_dir    = Path(os.environ.get("COVERS_DIR")    or str(_PROJECT_ROOT / "covers")).resolve()

if _downloads_dir.exists():
    app.mount("/downloads", StaticFiles(directory=str(_downloads_dir)), name="downloads")

if _covers_dir.exists():
    app.mount("/covers", StaticFiles(directory=str(_covers_dir)), name="covers")


# ── Playlists ────────────────────────────────────────────────────────────────

@app.get("/api/playlists")
def get_playlists():
    """Returns all playlists with full info."""
    import sqlite3
    with sqlite3.connect(_db_path) as conn:
        rows = conn.execute(
            "SELECT id, name, owner, total_tracks, snapshot_id, last_synced_at FROM playlists"
        ).fetchall()
    return [
        {
            "id": r[0],
            "name": r[1],
            "owner": r[2],
            "total_tracks": r[3],
            "snapshot_id": r[4],
            "last_synced_at": r[5],
        }
        for r in rows
    ]


@app.get("/api/playlists/{playlist_id}/tracks")
def get_playlist_tracks(playlist_id: str):
    tracks = db.get_playlist_tracks(playlist_id)
    if not tracks and not _playlist_exists(playlist_id):
        raise HTTPException(status_code=404, detail="Playlist not found")
    for t in tracks:
        t["audio_url"] = f"/api/audio/{t['id']}" if t.get("downloaded") else None
        t["cover_url"] = f"/api/album-cover/{t['album_id']}" if t.get("album_id") else None
    return tracks


# ── Tracks ────────────────────────────────────────────────────────────────────

@app.get("/api/tracks")
def get_all_tracks():
    tracks = db.get_all_unique_tracks()
    for t in tracks:
        t["audio_url"] = f"/api/audio/{t['id']}" if t.get("downloaded") else None
    return tracks


@app.get("/api/tracks/{track_id}")
def get_track(track_id: str):
    t = db.get_track(track_id)
    if not t:
        raise HTTPException(status_code=404, detail="Track not found")
    return t


@app.get("/api/audio/{track_id}")
def stream_audio(track_id: str):
    """Stream the mp3 for a track."""
    import sqlite3
    with sqlite3.connect(_db_path) as conn:
        row = conn.execute(
            "SELECT file_path, downloaded FROM tracks WHERE id = ?", (track_id,)
        ).fetchone()

    if not row or not row[1] or not row[0]:
        raise HTTPException(status_code=404, detail="Audio not downloaded")

    fp = Path(row[0])
    if not fp.exists():
        raise HTTPException(status_code=404, detail="Audio file missing on disk")

    return FileResponse(str(fp), media_type="audio/mpeg", filename=fp.name)


# ── Albums / Covers ───────────────────────────────────────────────────────────

@app.get("/api/albums/{album_id}")
def get_album(album_id: str):
    album = db.get_album(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    album["cover_url"] = f"/api/album-cover/{album_id}"
    return album


@app.get("/api/album-cover/{album_id}")
def get_album_cover(album_id: str):
    """Serve local cover art if available, otherwise 404."""
    for ext in ("jpg", "jpeg", "png", "webp"):
        candidate = _covers_dir / f"{album_id}.{ext}"
        if candidate.exists():
            return FileResponse(str(candidate))
    raise HTTPException(status_code=404, detail="Cover not found")


# ── Stats ─────────────────────────────────────────────────────────────────────

@app.get("/api/stats")
def get_stats():
    return db.get_statistics()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _playlist_exists(playlist_id: str) -> bool:
    import sqlite3
    with sqlite3.connect(_db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM playlists WHERE id = ?", (playlist_id,)
        ).fetchone()
    return row is not None


# ── Jobs ──────────────────────────────────────────────────────────────────────

@app.post("/api/sync")
def trigger_sync():
    """Start a background Spotify → DB sync. Returns 409 if already running."""
    if _job_state["status"] == "running":
        raise HTTPException(status_code=409, detail="A job is already running")

    def _sync():
        from controllers.app import sync_spotify_to_database
        sync_spotify_to_database()

    t = threading.Thread(target=_run_job, args=("sync", _sync), daemon=True)
    t.start()
    return {"status": "started"}


@app.post("/api/download")
def trigger_download():
    """Start a background download of all pending tracks."""
    if _job_state["status"] == "running":
        raise HTTPException(status_code=409, detail="A job is already running")

    def _download():
        from download_tracks import download_all_tracks
        download_all_tracks(max_downloads=None)

    t = threading.Thread(target=_run_job, args=("download", _download), daemon=True)
    t.start()
    return {"status": "started"}


@app.get("/api/jobs/status")
def job_status():
    return dict(_job_state)


@app.get("/api/jobs/logs")
def job_logs():
    """SSE stream — sends log lines as they arrive, then keeps connection alive."""
    def event_stream():
        while True:
            try:
                line = _log_queue.get(timeout=30)
                with _job_lock:
                    _job_state["logs"].append(line)
                yield f"data: {line}\n\n"
            except queue.Empty:
                # keepalive comment
                yield ": ping\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


# ── UI ────────────────────────────────────────────────────────────────────────

_static_dir = Path(__file__).parent / "static"
_static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
def serve_ui():
    index = _static_dir / "index.html"
    if not index.exists():
        return HTMLResponse("<h1>UI not found</h1>", status_code=404)
    return HTMLResponse(index.read_text())


