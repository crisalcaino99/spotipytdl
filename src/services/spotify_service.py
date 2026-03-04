import spotipy
from spotipy.oauth2 import SpotifyOAuth

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class SpotifyService:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.sp = None
    
    def authenticate(self):
        """Autentica Spotify usando OAuth"""
        scope = 'playlist-read-private playlist-read-collaborative'
        
        auth_manager = SpotifyOAuth(
            client_id = self.client_id, 
            client_secret = self.client_secret,
            redirect_uri= self.redirect_uri,
            scope=scope
        )

        self.sp = spotipy.Spotify(auth_manager=auth_manager)
        print('-Autenticado-')
    
    def get_user_playlists(self) -> dict:
        """Obtiene todas las playlists del usuario"""
        if not self.sp:
            self.authenticate()

        playlists = []
        results = self.sp.current_user_playlists()
        
        while results:
            for item in results['items']:
                details = self.sp.playlist(item['id'], fields='id, snapshot_id')
                playlists.append({
                    'id': item['id'],
                    'name': item['name'],
                    'owner': item['owner']['display_name'],
                    'total_tracks': item['tracks']['total'],
                    'snapshot_id': details.get('snapshot_id', '')
                })
            
            if results['next']:
                results = self.sp.next(results)
            else:
                results = None
        
        return playlists
    
    def get_playlist_tracks(self, playlist_id: str):
        """Obtiene tracks de una playlist"""
        if not self.sp:
            self.authenticate()
        
        tracks = []
        snapshot_id = None
        results = self.sp.playlist_items(playlist_id)

        while results:
            if snapshot_id is None:
                snapshot_id = results.get('snapshot_id', '')

            for item in results['items']:
                track = item['track']
                # print(track)
                if track and track.get('id'):
                    artists = [a.get('name') for a in track.get('artists', []) if a and a.get('name')]
                    
                    if not artists:
                        artists = ['Unknown Artist'] 
                    
                    # modificattiones
                    album_info = track.get('album', {})

                    tracks.append({
                        'id': track['id'],
                        'name': track['name'],
                        'artists': artists,
                        'album': {
                            'id': album_info.get('id', ''),
                            'name': album_info.get('name', 'Unknown Album'),
                            'artist': album_info.get('artists', [{}])[0].get('name', 'Unknown'),
                            'cover_url': self._get_medium_cover(album_info.get('images', []))
                        }
                    })
            
            if results['next']:
                results = self.sp.next(results)
            else:
                results = None
        
        return tracks, snapshot_id
    
    # TODO: what type of object is an image?
    def _get_medium_cover(self, images):
        """Elige imagen de 300 x 300"""
        for img in images:
            if img.get('height') == 300:
                return img['url']
        
        return images[0]['url'] if images else None
    

if __name__ == '__main__':
    CLIENT_ID = '767bf032d25042e0a2246f1c10ebf0d7'
    CLIENT_SECRET = '655f4fc8750a4d1db6f0d75244facbb1'
    REDIRECT_URI = 'https://example.com/callback'

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
        print(f"\n Primeros 5 tracks:")

        for t in tracks[:5]:
            print(f"  - {t['name']} by {', '.join(t['artists'])}")
            print(f" Artistas {','.join(t['artists'])}")
            print(f" Album ID: {t['album']['name']}")
            print(f" Album artista {t['album']['artist']}")
            print(f" cover url {t['album']['cover_url']}" if t['album']['cover_url'] else " Cover URL None")

    
