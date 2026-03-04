from models.track import Track
from schemas.spotify_types import SpotifyPlaylistResponse


class Playlist:
    """Representacion de una playlist de Spotify"""

    def __init__(self, id: str, name: str, owner: str,
                total_tracks: int, snapshot_id: str = '') -> None:
        self.id = id
        self.name = name
        self.owner = owner
        self.total_tracks = total_tracks
        self.tracks: list[Track] = []
        self.snapshot_id = snapshot_id
    
    def __repr__(self) -> str:
        """Representacion en String del Objeto"""
        return f"Playlist {self.name}"
        

    def add_track(self, track: Track) -> None:
        self.tracks.append(track)
        return None
    
    def to_dict(self) -> dict[str, str | int]:
        """Pasar el objeto a diccionario"""
        return {
            'id': self.id,
            'name': self.name,
            'owner': self.owner,
            'total_tracks': self.total_tracks
        }
    
    from typing import Self
    @classmethod
    # TODO: Revisar la API de Spotify porque estoy seguro de que no funciona asi
    def from_spotify_response(cls, spotify_data: SpotifyPlaylistResponse) -> Self:
        """ Factory method """
        return cls(
            id = spotify_data['id'],
            name = spotify_data['name'],
            owner = spotify_data['owner']['display_name'],
            total_tracks = spotify_data['tracks']['total'],
            snapshot_id = spotify_data.get('snapshot_id', '')
        )
    

if __name__ == '__main__':
    fake_data = {
        'id': 'abc123',
        'name': 'Rock Classics',
        'owner': {'display_name': 'Juan'},
        'tracks': {'total': 50}
    }

    playlist = Playlist.from_spotify_response(fake_data) # type: ignore
    print(playlist)

    track1 = Track('1', 'Bohemian Rhapsody',['Queen'])
    track2 = Track('2','Stairway to Heaven',  ['Led Zeppelin'])

    playlist.add_track(track1)
    playlist.add_track(track2)

    print(f"Tracks agregados: {len(playlist.tracks)}")

    for track in playlist.tracks:
        print(f" - {track}")
