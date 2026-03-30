import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
from time import sleep

import requests


# TODO: aÑadir parametro de termino para el test
def scrape_covers(test_int: int) -> None:
    """Descarga covers de albumes que no la tienen"""
    
    covers_dir = Path('covers')
    covers_dir.mkdir(exist_ok=True)

    # TODO: usar with aqui
    # TODO: Mover la funcion para que sea en base a una playlist especifica
    conn = sqlite3.connect('music.db')
    cursor = conn.cursor()

    # TODO: Mover linea
    # Sacamos la tabla de las partes que no tengan cover
    cursor.execute("""
        SELECT id, name, artists, cover_url
        FROM albums
        WHERE cover_path IS NULL AND cover_url IS NOT NULL
        """)
    
    albums = cursor.fetchall()
    #TODO: Solo tomar los K esimos primeros de aca

    if not albums: 
        print('Todos los albums ya tienen covers descargados')
        conn.close()
        return None
    
    else:
        try:
            albums = albums[:test_int]
        except Exception:
            print("Ha ocurrido un error en linea 40")
            return None

    print(f"\n Descargando {len(albums)} covers ...")

    success = 0
    failed = 0

    for album_id, name, artist, cover_url in albums:
        print(f'{name}-{artist}...', end=" ")

        try:
            response = requests.get(cover_url, timeout=10)
            response.raise_for_status()

            cover_path = covers_dir / f"{album_id}.jpg"
            with open(cover_path, 'wb') as f:
                f.write(response.content)
            
            cursor.execute("""
                UPDATE albums
                SET cover_path = ?
                WHERE id = ?
            """, (str(cover_path), album_id))

            conn.commit()

            print(f" {len(response.content) // 1024} KB")
            success += 1

            sleep(0.1) # acorde a claude esto es para ser educado lol
        
        except Exception as e:
            print(f"Error {e}")
            failed += 1
    
    conn.close()
    print(f"\n {'='*50}")
    print(f" Exitosas {success}")
    print(f" Fallidas {failed}")
    print(f" Guardadas en {covers_dir.absolute()}")
    print(f"{'='*50}")
    return None

# testeo
if __name__ == "__main__":
    scrape_covers(50)

