from __future__ import annotations

from pathlib import Path

from mutagen.id3 import APIC, ID3, TIT2, error  # type: ignore

from schemas.spotify_types import AlbumData, TrackDict
from services.cover_service import ensure_album_cover_downloaded


def embed_metadata_for_track(
        track: TrackDict,
        album: AlbumData,
        cover_path: Path | None = None) -> bool:
    """Embebe metadata basica en un mp3
    
    Escribe
    -titulo
    -artistas
    -album
    -cover
    """
    file_path_str = track.get("file_path")
    if not file_path_str:
        return False
    
    file_path = Path(file_path_str)
    if not file_path.exists():
        return False
    
    try:
        try:
            tags = ID3(file_path)
        
        except error:
            # TODO: include debugging
            tags = ID3()
        
        tags.delall("TIT2")
        tags.delall("TPE1")
        tags.delall("TALB")
        tags.delall("APIC")

        title = track["name"]
        artists = ", ".join(track["artists"])
        album_name = album["name"]

        tags.add(TIT2(encoding=3, text=title))
        tags.add(TIT2(encoding=3, text=artists))
        tags.add(TIT2(encoding=3, text=album_name))
        
        if cover_path is not None and cover_path.exists():
            image_bytes = cover_path.read_bytes()
            tags.add(
                APIC(
                    encoding = 3,
                    mime = "image/jpeg",
                    type = 3,
                    desc = 'Cover',
                    data = image_bytes
                )
            )
            
        tags.save(file_path)
        return True
    
    except OSError:
        return False
    
    except ValueError:
        return False
    

def embed_metadata_for_album_tracks(
    album: AlbumData,
    tracks: list[TrackDict],
    covers_dir: Path) -> tuple[int, int]:
    
    """Embebe metadata para todos los tracks descargados de un album
    Devuelve: (success_count, failed_count)"""

    cover_path = ensure_album_cover_downloaded(album, covers_dir)
    success = 0
    failed = 0

    for track in tracks: 
        if not track.get("downloaded", False):
            continue

        if not track.get("file_path"):
            continue

        ok = embed_metadata_for_track(
            track=track, 
            album=album,
            cover_path=cover_path
        )

        if ok:
            success += 1
        else:
            failed += 1
    
    return success, failed

