from typing import TypedDict # noqa: I001

class AlbumSummary(TypedDict):
    id: str
    name: str
    artist: str
    has_cover: bool

class AlbumData(TypedDict):
    """Estructura de datos de un album desde Spotify
    id: str
    name: str
    artist: str
    cover_url: str"""
    id: str
    name: str
    artist: str
    cover_url: str

class TrackData(TypedDict):
    """Estructura de datos de un track desde Spotify
    id : str
    name: str
    artists: list[str]
    album: AlbumData """
    id: str
    name: str
    artists: list[str]
    album: AlbumData

class TrackDict(TypedDict):
    """Estructura auxiliar"""
    id: str
    name: str
    artists: list[str]
    album: str 
    downloaded: bool
    file_path: str | None
    

class PlaylistData(TypedDict):
    """Playlist data from Spotify API"""
    id: str
    name: str
    owner: str
    total_tracks: int
    snapshot_id: str

class PlaylistTrackDict(TypedDict):
    id: str
    name: str
    artists: list[str]
    album: str
    downloaded: bool
    file_path: str | None
    position: int

class SpotifyArtist(TypedDict):
    name: str

class SpotifyAlbum(TypedDict):
    id: str

class SpotifyTrackResponse(TypedDict):
    """"id: str
    name: str
    artists: list[SpotifyArtist]
    album: SpotifyAlbum"""
    id: str
    name: str
    artists: list[SpotifyArtist]
    album: SpotifyAlbum

class SpotifyOwner(TypedDict):
    display_name: str

class SpotifyTracks(TypedDict):
    total: int

class SpotifyPlaylistResponse(TypedDict):
    id: str
    name: str
    owner: SpotifyOwner
    tracks: SpotifyTracks
    snapshot_id: str