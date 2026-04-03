import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def add_file_path_column():
    """Agrega columna file_path a tracks"""
    conn = sqlite3.connect('music.db')
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(tracks)")          
    columns = [col[1] for col in cursor.fetchall()]

    if 'file_path' not in columns:
        cursor.execute("""
            ALTER TABLE tracks
            ADD COLUMN file_path TEXT
        """)
        conn.commit()
        print('Columna file_path agregada a tracks')
    
    else:
        print('file_path ya existe')
    conn.close()


def migrate_add_snapshot_column():
    """Agrega la columna snapshot_id a la tabla playlists"""
    # TODO: change this lol
    db_path = 'music.db'

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print('Aplicando migraciones')

    def check_column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]

        return (column in columns)

    try:
        if not check_column_exists(cursor, 'playlists', 'snapshot_id'):
            print('Agregando columna snapshot_id a playlists')
            cursor.execute("""
                ALTER TABLE playlists
                ADD COLUMN snapshot_id TEXT
            """)
            conn.commit()
            print('Migracion aplicada')
        
    except sqlite3.OperationalError as e:
        print(f"Error {e}")
    
    finally:
        conn.close()
        print('migracion completada lol')

if __name__ == "__main__":
    #migrate_add_snapshot_column()
    add_file_path_column()
