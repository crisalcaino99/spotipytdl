import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import Database
from models.playlist import Playlist
from models.track import Track
from services.spotify_service import SpotifyService


def sync_spotify_to_database() -> None:
    """ Sincroniza playlists de Spotify a la base de datos"""
    # Careful in here.
    
    # TODO: mover esto a variables de entorno
    CLIENT_ID = '767bf032d25042e0a2246f1c10ebf0d7'
    CLIENT_SECRET = '655f4fc8750a4d1db6f0d75244facbb1'
    REDIRECT_URI = 'https://example.com/callback'

    db = Database()
    spotify = SpotifyService(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
    spotify.authenticate()

    print('\n Obteniendo playlists de Spotify')
    spotify_playlists = spotify.get_user_playlists()

    local_snapshots = db.get_all_playlist_snapshots()
    changed_playlists = []
    new_playlists = [] 

    for playlist_data in spotify_playlists:
        pid = playlist_data['id']
        spotify_snap = playlist_data.get('snapshot_id')
        local_snap = local_snapshots.get(pid)

        if local_snap is None:
            new_playlists.append(playlist_data)
        elif local_snap != spotify_snap:
            changed_playlists.append(playlist_data)
    
    to_process = new_playlists + changed_playlists

    if not to_process:
        print('todo sincronizado')
        return
    
    for playlist_data in to_process:
        print(f" Procesando: {playlist_data['name']}")
        playlist = Playlist(
            id = playlist_data['id'],
            name = playlist_data['name'],
            owner = playlist_data['owner'],
            total_tracks = playlist_data['total_tracks'],
            snapshot_id= playlist_data.get('snapshot_id', ' ')
        )
        print(playlist.snapshot_id)

        db.save_playlist(playlist)
        tracks_data, snapshot_id = spotify.get_playlist_tracks(playlist_data['id'])
        print(f" {len(tracks_data)} tracks ")

        for position, track_data in enumerate(tracks_data):
            if not track_data.get('id'):
                print(" Track sin ID, saltando")
                continue
            
            if not track_data.get('artists'):
                print('Track sin artista')
                continue

            album_data = track_data['album']
            db.save_album(album_data)

            track = Track(id=track_data['id'], 
                        name = track_data['name'],
                        artists = track_data['artists'],
                        album_id = album_data['id'],
                    )
            db.save_track(track)
            db.link_track_to_playlist(playlist.id, track.id, position)
        
        print(" Guardado")

    print(" Sincronizacion completa! ")
    print(" Verificando base de datos ")
    first_playlist = playlist_data
    saved_tracks = db.get_playlist_tracks(first_playlist['id'])
    print(f"Playlist {first_playlist['name']} tiene {len(saved_tracks)}")
    
    return None


if __name__ == "__main__":
    sync_spotify_to_database()