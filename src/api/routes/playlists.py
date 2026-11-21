"""Playlist listing and detail endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from src.api.deps import get_db

router = APIRouter(prefix="/api/playlists", tags=["playlists"])


@router.get("")
def list_playlists() -> dict[str, Any]:
    """Summaries of every playlist stored locally."""
    return {"items": get_db().get_all_playlists_summary()}


@router.get("/{playlist_id}")
def get_playlist(playlist_id: str) -> dict[str, Any]:
    """One playlist plus its ordered tracks, including download state."""
    db = get_db()

    info = db.get_playlist_sync_info(playlist_id)
    if info is None:
        raise HTTPException(status_code=404, detail=f"playlist {playlist_id} not found")

    return {
        "playlist": info,
        "tracks": db.get_playlist_tracks(playlist_id),
    }
