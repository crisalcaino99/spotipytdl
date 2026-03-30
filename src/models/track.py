from typing import Any, Mapping, Self  # noqa: F401, I001 # pyright: ignore[reportUnusedImport]

from schemas.spotify_types import (  # noqa: F401
    SpotifyAlbum, # pyright: ignore[reportUnusedImport]
    SpotifyTrackResponse, # type: ignore
    SpotifyTracks,# pyright: ignore[reportUnusedImport]
)

class Track:
    def __init__(self, id: str, name: str,
            artists: list[str], album_id: str = '') -> None:
        self.id = id
        self.name = name
        self.artists = artists or ['Unknown Artist']
        self.album_id = album_id

    def __repr__(self) -> str:
        """Representacion en String del Objeto"""
        string_of_artists = self.artists
        if isinstance(self.artists, list): # type: ignore
            string_of_artists = ''
            for item in self.artists:
                string_of_artists += item 
                string_of_artists += ', '
            string_of_artists = string_of_artists[:-2]

        return f'{self.id} y {self.name}, artistas: {string_of_artists}'
    
    def to_dict(self) -> dict[str, str | list[str]]:
        return {
            'id': self.id,
            'name': self.name,
            'artists': self.artists,
            'album_id': self.album_id
        }
    
    @classmethod
    def from_spotify_response(cls, spotify_data: SpotifyTrackResponse) -> Self:
        artistas_raw = spotify_data.get("artists", [])

        list_of_artists: list[str] = [
            a.get("name", "Unknown Artist")
            for a in artistas_raw
        ]
        
        if not list_of_artists:
            list_of_artists = ['Unknown Artist']
        
        album = spotify_data.get('album', {})
        album_id = str(album.get('id', ''))

        return cls(
            id = spotify_data['id'],
            name = spotify_data['name'],
            artists = list_of_artists,    
            album_id = album_id
        )
    
# Test
if __name__ == '__main__':
    track1 = Track(
        id = '123',
        name = 'Imagine',
        artists = ['John Lennon'],
        album_id = '66oiw3898493209'
    )

    print('Test 1 - Constructor')
    print(track1)
    print()

    fake_spotify_data = {
        'id' : 'abc456',
        'name': 'Bohemian Rhapsody',
        'artists': [
            {'name': 'Queen', 'id': 'xyz'}
        ],
        'album': {
            'name': 'A night at the Opera',
            'id': 'album123'
        },
        'duration_ms': 354000,
        'external_urls': {
            'spotify': 'https://open.spotify.com/track/abc456'
        }
    }

    track2 = Track.from_spotify_response(fake_spotify_data) # type: ignore
    print('Test 2 - from_spotify_response.')
    print(track2)
    print(track2.to_dict())
    print()

    multi_artist_data = {
        'id' : 'multi123',
        'name' : 'Despacito',
        'artists': [
            {'name': 'Luis Fonsi'},
            {'name': 'Daddy Yankee'}
        ],
        'album': {'name': 'VIDA'},
        'duration_ms': 228826
    }
    
    track3 = Track.from_spotify_response(multi_artist_data) # type: ignore
    print('Test 3 - Multiple artistas')
    print(track3)
