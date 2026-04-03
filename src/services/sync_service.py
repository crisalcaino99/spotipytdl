from __future__ import annotations

from typing import Tuple

from src.database.db_manager import Database
from src.services.spotify_service import SpotifyService

# TODO: Completar esta funcion

def get_playlist_status(
        db: Database, 
        spotify: SpotifyService,
        playlist_id: str
) -> Tuple[str|None, str, str]:
    """Retorna el snapshot local, el snapshot remoto y el estado
    el estado es created, unchanged y changed"""
    
    status = ''

    local = db.get_playlist_sync_info(playlist_id)
    remote_snapshot = spotify.get_playlist_snapshot_id(playlist_id)

    if local is None:
        status = 'created'
        return (None, remote_snapshot, status)    

    # Fix error in here.
    elif local["snapshot_id"] == remote_snapshot:
        status = 'unchanged'
    
    else:
        status = 'changed'

    return (str(local['snapshot_id']), remote_snapshot, status)


def sync_playlist_if_needed(
        db: Database, 
        spotify: SpotifyService, 
        playlist_id: str
) -> str:
    
    remote_playlists = spotify.get_user_playlists()
    remote_playlist = next(
        (playlist for playlist in remote_playlists if playlist['id'] == playlist_id),
        None,
    )

    if remote_playlist is None:
        raise ValueError(f"Playlist no encontrada {playlist_id}")
    
    local_snapshots = db.get_all_playlist_snapshots()
    local_snapshot_id = local_snapshots.get(playlist_id)
    remote_snapshot_id = remote_playlist['snapshot_id']

    if local_snapshot_id == remote_snapshot_id:
        return 'unchanged'

    tracks, _ = spotify.get_playlist_tracks(playlist_id)

    db.save_playlist(remote_playlist)
    db.clear_playlist_tracks(playlist_id)

    for position, track in enumerate(tracks, start=1):
        db.save_album(track['album'])
        db.save_track(track)
        db.link_track_to_playlist(
            playlist_id = playlist_id,
            track_id = track['id'],
            position = position,
        )
        
    db.mark_playlist_as_synced(
        playlist_id = playlist_id,
        snapshot_id = remote_snapshot_id,
        total_tracks= remote_playlist['total_tracks']
    )

    if local_snapshot_id is None:
        return 'created'
    
    return 'updated'