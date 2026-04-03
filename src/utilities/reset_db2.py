import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
print(ROOT)
sys.path.insert(0, str(ROOT))

from src.database.db_manager import Database  # noqa: E402

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

    def clear_all_playlist_tracks(db_path: str) -> None:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM playlist_tracks")
    

    clear_all_playlist_tracks('music.db')

    db = Database('music.db')


    