"""Library statistics endpoint."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from src.api.deps import get_db

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
def get_stats() -> dict[str, Any]:
    """Counts across tracks, playlists and albums."""
    return get_db().get_statistics()
