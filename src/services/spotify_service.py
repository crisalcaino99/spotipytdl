import sys
from pathlib import Path
from typing import Any

import spotipy
from spotipy.oauth2 import SpotifyOAuth

sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas.spotify_types import AlbumData, PlaylistData, TrackData


class SpotifyService:
    def __init__(self, client_id: str|None, client_secret: str|None,
                redirect_uri: str|None):
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.sp = None
    
    def authenticate(self):
        """Autentica Spotify usando OAuth"""
        scope = 'playlist-read-private playlist-read-collaborative'
        
        if self.client_id is None or self.client_secret is None \
             or self.redirect_uri is None:
            raise TypeError('Algun valor de la instancia es None')

        auth_manager = SpotifyOAuth(
            client_id = self.client_id, 
            client_secret = self.client_secret,
            redirect_uri= self.redirect_uri,
            scope=scope
        )

        sp = spotipy.Spotify(auth_manager=auth_manager)
        print('-Autenticado-')
        return sp
    
    def get_user_playlists(self) -> list[PlaylistData]:
        """Obtiene todas las playlists del usuario"""
        if self.sp is None:
            self.sp = self.authenticate()

        playlists: list[PlaylistData] = []
        results: Any|None = self.sp.current_user_playlists()
        
        while results:
            for item in results['items']:
                details: Any = self.sp.playlist(item['id'], fields='id, snapshot_id')
                
                current_playlist: PlaylistData = {
                    'id': item['id'],
                    'name': item['name'],
                    'owner': item['owner']['display_name'],
                    'total_tracks': item['tracks']['total'],
                    'snapshot_id': details.get('snapshot_id', '')
                }
                playlists.append(current_playlist)
            
            if results['next']:
                results = self.sp.next(results)
            else:
                results = None
        
        return playlists
    
    def get_playlist_tracks(self, playlist_id: str) -> tuple[list[TrackData], Any]:
        """Obtiene tracks de una playlist
        tuple(tracks, snapshot)"""

        if self.sp is None:
            self.sp = self.authenticate()

        tracks: list[TrackData] = []
        snapshot_id = None
        results: Any = self.sp.playlist_items(playlist_id)

        while results:
            if snapshot_id is None:
                snapshot_id = results.get('snapshot_id', '')

            for item in results['items']:
                track = item['track']
                # print(track)
                if track and track.get('id'):
                    artists = [a.get('name') for a in track.get('artists', [])
                            if a and a.get('name')]
                    
                    if not artists:
                        artists = ['Unknown Artist'] 
                    
                    # modificattiones
                    album_info = track.get('album', {})

                    album_data: AlbumData = {
                            'id': album_info.get('id', ''),
                            'name': album_info.get('name', 'Unknown Album'),
                            'artist': album_info.get('artists', [{}])[0].get('name',
                                                                            'Unknown'),
                            'cover_url': self._get_medium_cover(album_info.get('images',
                                                                                []))
                        }
                    current_track: TrackData = {
                        'id': track['id'],
                        'name': track['name'],
                        'artists': artists,
                        'album': album_data
                    }

                    tracks.append(current_track)
            
            if results['next']:
                results = self.sp.next(results)
            else:
                results = None
        
        return tracks, snapshot_id
    
    def get_playlist_snapshot_id(self, playlist_id: str) -> str:
        if self.sp is None:
            self.sp = self.authenticate()
        
        details: Any = self.sp.playlist(playlist_id, fields='id, snapshot_id')
        return details.get("snapshot_id", '')


    # TODO: what type of object is an image?
    def _get_medium_cover(self, images: Any) -> str:
        """Elige imagen de 300 x 300"""
        for img in images:
            if img.get('height') == 300:
                return img['url']
        
        return images[0]['url'] if images else ''
    

def generate_sp_service() -> SpotifyService:
    
    import os

    from dotenv import load_dotenv
    load_dotenv()
    CLIENT_ID = str(os.getenv("SPOTIFY_CLIENT_ID"))
    CLIENT_SECRET = str(os.getenv("SPOTIFY_CLIENT_SECRET"))
    REDIRECT_URI = str(os.getenv("SPOTIFY_REDIRECT_URI"))

    return SpotifyService(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)

if __name__ == '__main__':
    
    import os

    from dotenv import load_dotenv
    # maybe i need the path

    env_path = Path(__file__).resolve().parent.parent / '.env'
    print(env_path)
    load_dotenv(env_path)


    CLIENT_ID = str(os.getenv("SPOTIFY_CLIENT_ID"))
    CLIENT_SECRET = str(os.getenv("SPOTIFY_CLIENT_SECRET"))
    REDIRECT_URI = str(os.getenv("SPOTIFY_REDIRECT_URI"))

    print(CLIENT_ID)
    print(CLIENT_SECRET)
    print(REDIRECT_URI)

    try:
        service = SpotifyService(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
        service.authenticate()
        playlists = service.get_user_playlists()
        print(f"\n📋 Encontradas {len(playlists)} playlists:")
        for p in playlists[:5]:
            print(f"  - {p['name']} ({p['total_tracks']} tracks)")
        
        # Obtener tracks de la primera playlist
        if playlists:
            first_playlist = playlists[0]
            print(first_playlist)
            print(f"\n🎵 Tracks de '{first_playlist['name']}':")
            
            tracks, snapshot_id = service.get_playlist_tracks(first_playlist['id'])

            print(f"Snapshot ID {snapshot_id}")
            print(f"\n Primeros 5 tracks:")  # noqa: F541

            for t in tracks[:5]:
                print(f"  - {t['name']} by {', '.join(t['artists'])}")
                print(f" Artistas {','.join(t['artists'])}")
                print(f" Album ID: {t['album']['name']}")
                print(f" Album artista {t['album']['artist']}")
                print(f" cover url {t['album']['cover_url']}" 
                    if t['album']['cover_url'] else " Cover URL None")

    except Exception as e:
        print(e)
        print("Error de autenticacion")
        
    
    