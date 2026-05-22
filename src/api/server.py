import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database.db_manager import Database

app = FastAPI(
    title="Spotipyt",
    description="Local music library server",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_db_path = os.environ.get("DB_PATH", "music.db")
db = Database(_db_path)

_downloads_dir = Path(os.environ.get("DOWNLOADS_DIR", "downloads")).resolve()
_covers_dir = Path(os.environ.get("COVERS_DIR", "covers")).resolve()

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


