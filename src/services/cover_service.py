from __future__ import annotations

from pathlib import Path
from typing import Final

import requests

from schemas.spotify_types import AlbumData

DEFAULT_TIMEOUT: Final[int] = 10

def ensure_album_cover_downloaded(
        album: AlbumData,
        covers_dir: Path,
        timeout: int = DEFAULT_TIMEOUT
) -> Path | None:
    """Asegura que el cover del album exista localmente.
    Si ya existe lo reutiliza
    Si no hay cover_url devuelve None"""

    cover_url = album.get("cover_url")
    
    if not cover_url:
        return None
    
    covers_dir.mkdir(parents=True, exist_ok=True)

    cover_path = covers_dir / f"{album['id']}.jpg"
    if cover_path.exists():
        return cover_path

    response = requests.get(cover_url, timeout=timeout)
    response.raise_for_status()

    cover_path.write_bytes(response.content)
    return cover_path

