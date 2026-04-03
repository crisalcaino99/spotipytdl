from models.track import Track
from schemas.spotify_types import SpotifyPlaylistResponse


class Playlist:
    """Representacion de una playlist de Spotify"""
    def __init__(self, id: str, name: str, owner: str,
                total_tracks: int, snapshot_id: str = '',
                last_synced_at: str|None = None) -> None:
        self.id = id
        self.name = name
        self.owner = owner
        self.total_tracks = total_tracks
        self.snapshot_id = snapshot_id
        self.last_synced_at = last_synced_at
    
    def __repr__(self) -> str:
        """Representacion en String del Objeto"""
        return f"Playlist {self.name}"
        
    # add track method deleted

    def to_dict(self) -> dict[str, str | int]:
        """Pasar el objeto a diccionario"""
        return {
            'id': self.id,
            'name': self.name,
            'owner': self.owner,
            'total_tracks': self.total_tracks,
            'snapshot_id': self.snapshot_id,
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

    