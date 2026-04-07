#Bingo: Include this into the CLI or pipeline of export and voila!
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from mutagen.id3 import ID3
from mutagen.id3._frames import APIC, TALB, TIT2, TPE1
from mutagen.id3._util import error

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
from src.schemas.spotify_types import TrackDict  # noqa: E402


def embed_metadata_for_file(
        track: TrackDict,
        cover_path: Path | None ) -> bool:
    
    """Embebe metadata basica en un mp3
    
    Escribe
    -titulo
    -artistas
    -album
    -cover
    """
    file_path_str = track.get("file_path")
    if not file_path_str:
        return False
    
    file_path = Path(file_path_str)
    if not file_path.exists():
        return False
    
    try:
        try:
            tags = ID3(file_path)
        
        except error:
            # TODO: include debugging
            tags = ID3()
        
        tags.delall("TIT2")
        tags.delall("TPE1")
        tags.delall("TALB")
        tags.delall("APIC")

        title = track["name"]
        artists = ", ".join(track["artists"])
        album_name = track["album"]

        tags.add(TIT2(encoding=3, text=title))
        tags.add(TPE1(encoding=3, text=artists))
        tags.add(TALB(encoding=3, text=album_name))
        
        if cover_path is not None and cover_path.exists():
            image_bytes = cover_path.read_bytes()
            tags.add(
                APIC(
                    encoding = 3,
                    mime = "image/jpg",
                    type = 3,
                    desc = 'Cover',
                    data = image_bytes
                )
            )
            
        tags.save(file_path, v2_version=3)
        return True
    
    except OSError:
        return False
    
    except ValueError:
        return False

def test_embed_metadata_for_file() -> None:
    root = Path(__file__).resolve().parent
    assets_dir = root / 'assets'
    debug_dir = root / 'debug_output'

    debug_dir.mkdir(parents=True, exist_ok=True)

    source_mp3 = assets_dir / 'sample.mp3'
    source_cover = assets_dir / 'cover.jpg'

    assert source_mp3.exists(), f'Missing test mp3: {source_mp3}'
    assert source_cover.exists(), f'Missing test cover: {source_cover}'

    test_mp3 = debug_dir / 'sample_tagged.mp3'
    test_cover = debug_dir / 'cover.jpg'

    shutil.copy2(source_mp3, test_mp3)
    assert test_mp3.exists()
    shutil.copy2(source_cover, test_cover)

    track: TrackDict = {
        'id': 'track_001',
        'name': 'Test Song',
        'artists': ['Test Artist 1', 'Test Artist 2'],
        'album': 'Test Album',
        'album_id': '001',
        'downloaded': True, 
        'file_path': '',
    }
    
    track['file_path'] = str(test_mp3)

    ok = embed_metadata_for_file(
        track = track,
        cover_path = test_cover,
    )

    assert ok is True

    tags = ID3(test_mp3)

    assert tags.get('TIT2') is not None
    assert str(tags['TIT2']) == 'Test Song'

    assert tags.get('TPE1') is not None
    assert str(tags['TPE1']) == 'Test Artist 1, Test Artist 2'

    assert tags.get('TALB') is not None
    assert str(tags['TALB']) == 'Test Album'

    apic_frames = tags.getall('APIC')
    assert len(apic_frames) == 1
    assert apic_frames[0].mime in {'image/jpeg', 'image/jpg', 'image/png'}
    assert len(apic_frames[0].data) > 0




