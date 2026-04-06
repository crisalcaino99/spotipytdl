from __future__ import annotations

import sqlite3
from pathlib import Path
from time import sleep

import requests

from database.db_manager import Database


def download_cover_bytes(url: str, timeout: int = 10) -> bytes:
    response = requests.get(url, timeout = timeout)
    response.raise_for_status()
    return response.content

def save_cover_image(image_bytes:bytes, cover_path: Path) -> None:
    """Write the bytes to a path"""
    cover_path.parent.mkdir(parents=True, exist_ok=True)
    cover_path.write_bytes(image_bytes)

def ensure_album_cover(
    db: Database, 
    album_id: str, 
    covers_dir: Path,
) -> Path | None:
    """Verifica que el album (tabla) tenga el cover. Si no, lo descarga"""

    covers_dir.mkdir(parents=True, exist_ok = True)

    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, cover_url, cover_path
            FROM albums
            WHERE id = ?
            """,
            (album_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None
    
        db_album_id, cover_url, cover_path_str = row

        # Revisa si existe el cover descargado
        # Si existe entonces termina
        if cover_path_str:
            existing_cover_path = Path(cover_path_str)
            if existing_cover_path.exists():
                return existing_cover_path

        if not cover_url:
            return None

        response = requests.get(cover_url, timeout = 10)
        response.raise_for_status()

        cover_path = covers_dir / f"{db_album_id}.jpg"
        cover_path.write_bytes(response.content)

        update_album_cover_path(conn, db_album_id, cover_path)
        return cover_path
    
def fetch_albums_missing_covers(conn: sqlite3.Connection,
                                limit: int | None = None) -> list[tuple[str, str, str, str]]:  # noqa: E501
    
    # Seleccionamos los albumes tal que no tienen cover pero si tienen link
    query = """
        SELECT id, name, artists, cover_url
        FROM albums
        WHERE cover_path IS NULL
        AND cover_url IS NOT NULL
    """
    params: tuple[int, ...] = ()

    if limit is not None:
        query += "\nLIMIT ?"
        params = (limit, )

    cursor = conn.execute(query, params)
    return cursor.fetchall()

def update_album_cover_path(
        conn: sqlite3.Connection,
        album_id: str,
        cover_path: Path
) -> None:
    """Modifica un album para cambiar la direccion de su cover path"""
    conn.execute(
        """
        UPDATE albums
        SET cover_path = ?
        WHERE id = ?
        """,
        (str(cover_path), album_id)
    )

def scrape_covers(
        db_path: Path, 
        covers_dir: Path,
        limit: int | None = None,
        polite_sleep_seconds: float = 0.1) -> None:
    """Saca las covers uniendo las funciones"""
    covers_dir.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        albums = fetch_albums_missing_covers(conn, limit = limit)

        if not albums: 
            print("Todos los albums ya tienen covers descargados")
            return
        
        print(f"\n Descargando {len(albums)} covers...")

        success = 0
        failed = 0

        for album_id, name, artist, cover_url in albums:
            print(f"{name} - {artist}...", end=" ")

            try:
                image_bytes = download_cover_bytes(cover_url)
                cover_path = covers_dir / f"{album_id}.jpg"

                save_cover_image(image_bytes, cover_path)
                update_album_cover_path(conn, album_id, cover_path)

                success +=1
                sleep(polite_sleep_seconds)
            
            except requests.RequestException:
                # TODO: out of good will I should write logging as for the mistake
                failed += 1
            
            except OSError:
                failed += 1

            except sqlite3.Error:
                failed += 1
        
        conn.commit()
    
    print(f"\n{'=' * 50}")
    print(f"Exitosas: {success}")
    print(f"Fallidas: {failed}")
    print(f"Guardadas en {covers_dir.absolute()}")
    print(f"{'=' * 50}")
