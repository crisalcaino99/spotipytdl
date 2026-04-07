import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.metadata_service import embed_metadata_for_track
from src.database.db_manager import Database
from src.schemas.spotify_types import TrackDict
from src.services.yt_service import Downloader

# TODO: Crear funcion que descarga desde la playlist
# TODO: Mover esto a utilities

def download_all_tracks(max_downloads: None|int):
    db = Database('music.db')
    # TODO: parametrizar esta linea eventualmente
    download_folder = Path(__file__).resolve().parent.parent / "downloads"
    youtube = Downloader(download_dir= download_folder, ffmpeg_location=None)

    all_tracks = db.get_all_unique_tracks()
    pending = [t for t in all_tracks if not t['downloaded']]

    if max_downloads:
        pending = pending[:max_downloads]
        print(f"Limite: solo descargando {len(pending)}")
    
    if not pending:
        print('todo descargado')
        return
    
    success = 0
    failed = 0

    for i, track in enumerate(pending, 1):
        print(f"\n [{i}/ {len(pending)}] {track['name']} - {track['artists']}")

        artists = track['artists']
        result = ', '.join(artists)
        file_path = youtube.search_and_download(track['name'], result)

        if file_path:
            db.mark_as_downloaded(track['id'], file_path)
            success += 1
        
        else: 
            failed += 1
    
    print(f"Exitosos {success}")
    print(f"Fallidos {failed}")

# some test lol
# TODO: FIX THIS ASAP
# this one is sooooo wrong
def download_single_track(track: TrackDict) -> str | None:

    from src.services.scrape_covers_v2 import ensure_album_cover

    db = Database('music.db')
    artists = track['artists']
    result = ', '.join(artists)
    
    download_folder = Path(__file__).resolve().parent.parent / "downloads"
    youtube = Downloader(download_dir = download_folder, ffmpeg_location=None)
    file_path = youtube.search_and_download(track['name'], result)
    
    if file_path:
        # marco el track como descargado y señalo su path
        # Si tengo el archivo deberia asegurarme de tengo el path bien puesto o no
        db.mark_as_downloaded(track['id'], file_path)
    
        covers_path = Path(__file__).resolve().parent.parent / "covers"
        cover_track_path = ensure_album_cover(db, album_id = track['album_id'],
                        covers_dir = covers_path)
        
        # Insert method to modify track ->
        # Por alguna razon no esta funcionando
        embed_metadata_for_track(track=track, cover_path=cover_track_path)

    return file_path

#TODO: FIX THIS THING
#TODO: Include the ensure cover thing
def download_pending_tracks_from_playlist(playlist_id: str) -> dict[str, int]:


    db = Database('music.db')
    tracks = db.get_playlist_tracks(playlist_id)

    pending_tracks = [t for t in tracks if not t.get("downloaded")]

    downloaded = 0
    failed = 0
    skipped = len(tracks) - len(pending_tracks)

    for track in pending_tracks:
        track_dict = TrackDict(track)
        track_dict.pop("position", None)

        # TODO: Include the ensure type thing
        # Some really bad solution would be to look up for the album_id the track 
        # belongs
        # to. 
        # You could do the research in there 

        result = download_single_track(track_dict)

        if result:
            downloaded += 1
        else:
            failed +=1

    return {
        'downloaded': downloaded, 
        'failed': failed,
        'skipped': skipped,
    }


if __name__ == '__main__':
    download_all_tracks(max_downloads=1)

