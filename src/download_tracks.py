import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import Database
from services.yt_service import YoutubeService

# TODO: Crear funcion que descarga desde la playlist
# TODO: Mover esto a utilities
def download_all_tracks(max_downloads = None or int):
    db = Database('music.db')
    # TODO: parametrizar esta linea eventualmente
    youtube = YoutubeService(download_dir='downloads')

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

        file_path = youtube.search_and_download(track['name'], track['artists'])

        if file_path:
            db.mark_as_downloaded(track['id'], file_path)
            success += 1
        
        else: 
            failed += 1
    
    print(f"Exitosos {success}")
    print(f"Fallidos {failed}")

# some test lol
if __name__ == '__main__':
    download_all_tracks(max_downloads=5)