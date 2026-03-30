from dataclasses import dataclass


@dataclass
class TrackMetadata:
    title: str
    artist: str
    album: str | None
    track_number: int | None

