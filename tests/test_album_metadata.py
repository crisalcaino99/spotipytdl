from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

print("Here =", HERE)
print("Root =", ROOT)
print("SRC =", SRC)
print("Exists SRC =", SRC.exists())
sys.path.insert(0, str(SRC))
print(sys.path[:3])

from database.db_manager import Database  # noqa: E402
from schemas.spotify_types import AlbumSummary  # noqa: E402
from services.album_processing import process_album_metadata  # noqa: E402


def main() -> None:
    db = Database("music.db")

    albums: list[AlbumSummary]|None = db.get_all_albums_summary()

    if not albums:
        print("No hay albumes en la base de datos.")
        return
    
    print("\n Albumes disponibles \n")

    for i, album in enumerate(albums, start = 1):
        cover = "tic" if album["has_cover"] else "no"
        print(f"{i}. {album['name']} - {album['artist']} [{cover}]")

    choice = input("\n Selecciona un album:").strip()

    if not choice.isdigit():
        print("Entrada invalida.")
        return
    
    index = int(choice) - 1

    if index < 0 or index >= len(albums):
        print("out of range lol")
        return
    
    album_id = albums[index]['id']
    print(album_id)

    # Hay un error con esta funcion
    succcess, failed = process_album_metadata(
        db = db,
        album_id = album_id,
        covers_dir = Path("covers")
    )

    print(f"Success {succcess}")
    print(f"Failed {failed}")
    
    return None

if __name__ == "__main__":
    main()