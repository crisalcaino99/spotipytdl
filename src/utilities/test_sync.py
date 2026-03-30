from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
print(ROOT)
sys.path.insert(0, str(ROOT))

from src.database.db_manager import Database  # noqa: E402
from src.services.spotify_service import SpotifyService  # noqa: E402
from src.services.sync_service import sync_playlist_if_needed  # noqa: E402

if __name__ == '__main__':
    
    import os

    from dotenv import load_dotenv
    load_dotenv(ROOT / 'src'/'.env')

    client_id_var = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret_var = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri_var = os.getenv("SPOTIFY_REDIRECT_URI")

    print(client_id_var)
    print(client_secret_var)
    print(redirect_uri_var)
    
    db = Database('music_test.db')
    spotify = SpotifyService(client_id=client_id_var,
                            client_secret=client_secret_var,
                            redirect_uri=redirect_uri_var)
    spotify.authenticate()

    playlists = spotify.get_user_playlists()
    playlist_id = playlists[0]['id']

    result = sync_playlist_if_needed(db, spotify, playlist_id)
    print(result)
