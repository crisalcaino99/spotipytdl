from __future__ import annotations

from pathlib import Path

from database.db_manager import Database
from schemas.spotify_types import AlbumData
from services.metadata_service import embed_metadata_for_album_tracks


def process_album_metadata(
    db: Database,
    album_id: str, 
    covers_dir: Path) -> tuple[int, int]:
    """Dada la base de datos
    un id de album y una direccion 
    saca el album en la tabla, saca sus tracks y para cada uno les mete su metadata"""
    
    album: AlbumData | None = db.get_album(album_id)
    if album is None:
        raise ValueError(f"No se econtro el album con {album_id}")
    
    tracks = db.get_album_tracks(album_id)
    if not tracks: 
        return (0, 0)
    
    return embed_metadata_for_album_tracks(
        album = album, 
        tracks = tracks, 
        covers_dir = covers_dir 
    )

