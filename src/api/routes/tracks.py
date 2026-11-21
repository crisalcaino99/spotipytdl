"""Track listing and search endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from src.api.deps import get_db

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

    items = db.search_tracks(q) if q else db.get_all_unique_tracks()

    if downloaded is not None:
        items = [track for track in items if bool(track.get("downloaded")) is downloaded]

    total = len(items)

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items[offset: offset + limit],
    }
