from __future__ import annotations

import shutil
from pathlib import Path

from schemas.spotify_types import PlaylistTrackDict


def write_m3u8_playlist(
        playlist_name: str, 
        tracks: list[PlaylistTrackDict],
        output_dir: Path
) -> Path:
    """Dado una playlist y un track_paths y output dir
    escribe el .m3u8 de la playlist"""

    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(
        char for char in playlist_name if char not in '<>:*"/\\|?'
    ).strip()
    
    if not safe_name:
        safe_name = "playlist"

    playlist_path: Path = output_dir / f"{safe_name}.m3u8"

    lines: list[str] = ["#EXTM3U"]
    tracks_sorted = sorted(tracks, key = lambda t: t['position'])

    for track in tracks_sorted:
        file_path = track.get("file_path")
        if not file_path:
            continue
        lines.append(f"#EXTINF: -1, {', '.join(track['artists'])} - {track['name']}")
        lines.append(file_path)
        
    playlist_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return playlist_path

def export_playlist_bundle(
        playlist_name: str, 
        tracks: list[PlaylistTrackDict],
        export_root: Path,
) -> bool:
    
    """ Exporta una playlist como bundle portable
    Estructura:
    export_root/
        playlists/
        tracks/
    """
    
    bundle_dir = export_root 
    playlists_dir = bundle_dir / "playlists"
    tracks_dir = bundle_dir / "tracks"

    playlists_dir.mkdir(parents = True, exist_ok=True)
    tracks_dir.mkdir(parents=True, exist_ok=True)

    tracks_sorted = sorted(tracks, key=lambda track: track['position'])
    exported_tracks: list[PlaylistTrackDict] = []


    for track in tracks_sorted:
        source_path_str = track.get('file_path')
        if not source_path_str:
            continue

        source_path = Path(source_path_str)
        if not source_path.exists():
            continue
        
        destination_filename = f"{track['position']:03d} - {source_path.name}"
        destination_path = tracks_dir / destination_filename

        try:
            shutil.copy2(source_path, destination_path)
        
        except Exception as e:
            raise e
        


        exported_track: PlaylistTrackDict = {
            'id' : track['id'],
            'name': track['name'],
            'artists': track['artists'],
            'album': track['album'],
            'downloaded': track['downloaded'],
            'file_path': str(Path("..") / 'tracks'/ destination_path.name),
            'position': track['position']
        }

        exported_tracks.append(exported_track)
    
    try:
        write_m3u8_playlist(playlist_name=playlist_name,
                        tracks=exported_tracks,
                        output_dir=playlists_dir)
        return True
    
    except Exception as e:
        raise e

