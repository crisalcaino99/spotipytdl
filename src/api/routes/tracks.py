"""Track listing and search endpoints."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from src.api.deps import get_db

PROJECT_ROOT = Path(__file__).resolve().parents[3]

router = APIRouter(prefix="/api/tracks", tags=["tracks"])


@router.get("")
def list_tracks(
    q: str | None = Query(None, description="Substring search over name/artist/album"),
    downloaded: bool | None = Query(None, description="Filter by download state"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """List tracks from the local database, paginated."""
    db = get_db()

    items = db.get_all_unique_tracks()

    if q:
        needle = q.lower()
        items = [
            track for track in items
            if needle in track["name"].lower()
            or needle in (track["album"] or "").lower()
            or any(needle in artist.lower() for artist in track["artists"])
        ]

    if downloaded is not None:
        items = [track for track in items if bool(track.get("downloaded")) is downloaded]

    total = len(items)

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items[offset: offset + limit],
    }


@router.get("/{track_id}/audio")
def stream_audio(track_id: str) -> FileResponse:
    """Serve the local audio file for a track.

    Starlette's FileResponse answers Range requests, so seeking works in the
    browser without writing any range-handling code here.
    """
    raw_path = get_db().get_track_file_path(track_id)
    if not raw_path:
        raise HTTPException(status_code=404, detail="track has no local file")

    path = Path(raw_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    if not path.exists():
        raise HTTPException(status_code=404, detail="file is missing on disk")

    return FileResponse(path, filename=path.name)
