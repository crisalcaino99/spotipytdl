import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3  # noqa: I001

from models.playlist import Playlist
from models.track import Track
from schemas.spotify_types import AlbumData, TrackData, AlbumSummary, TrackDict


class Database:
    #TODO: Usar with en el codigo
    def __init__(self, db_path: str = 'music.db') -> None:
        self.db_path = db_path
        self.create_tables()
    
    def create_tables(self) -> None:
        """Crea las tablas si no existen"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS albums(
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL, 
                        artists TEXT NOT NULL,
                        cover_url TEXT, 
                        cover_path TEXT, 
                        track_count INTEGER DEFAULT 0
                        )
                """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tracks(
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL, 
                        artists TEXT NOT NULL,
                        album_id TEXT,
                        downloaded INTEGER DEFAULT 0,
                        file_path TEXT,
                        FOREIGN KEY (album_id) REFERENCES albums(id)
                    )
                """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS playlists(
                    id TEXT PRIMARY KEY, 
                    name TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    total_tracks INTEGER,
                    snapshot_id TEXT 
                )
            """
            )

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS playlist_tracks (
                        playlist_id TEXT NOT NULL,
                        track_id TEXT NOT NULL,
                        position INTEGER,
                        PRIMARY KEY (playlist_id, track_id),
                        FOREIGN KEY (playlist_id) REFERENCES playlists(id),
                        FOREIGN KEY (track_id) REFERENCES tracks(id)
                )
            """
            )
            
            conn.commit()
            conn.close()
        return None

    def save_track(self, track: TrackData) -> None:
        """Guarda un track en la BD"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            artists_str = ', '.join(track["artists"])
            cursor.execute("""
                INSERT INTO tracks (id, name, artists, album_id)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name, 
                        artists = excluded.artists, 
                        album_id = excluded.album_id
            """, (
                track["id"],
                track["name"],
                artists_str,
                track["album"]["id"]
            ))

        return None
    
    def save_album(self, album_data: AlbumData) -> None:
        """Guarda o actualiza un album"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(""" 
                INSERT OR REPLACE INTO albums (id, name, artists, cover_url)
                VALUES (?, ?, ?, ?)
            """, (
                album_data['id'],
                album_data['name'],
                album_data['artist'],
                album_data['cover_url']
            ))

            conn.commit()
            conn.close()
        return None
    
    def get_track(self, track_id: str) -> dict[str, str] | None:
        """Obtiene un track por ID. Retorna dict o None"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, artists, album_id
                FROM tracks
                WHERE id = ?
            """, (track_id, ))

            row = cursor.fetchone()
            
            conn.close()

            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'artists': row[2],
                    'album': row[3]
                }
            
        return None
    
    def save_playlist(self, playlist: Playlist) -> None:
        """Guarda una playlist en la BD"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE 
                INTO playlists (id, name, owner, total_tracks, snapshot_id)
                VALUES (?, ?, ?, ?, ?)
            """, 
            (playlist.id, playlist.name, playlist.owner,
            playlist.total_tracks, playlist.snapshot_id))

            conn.commit()
            conn.close()
        return None

    def link_track_to_playlist(self, playlist_id: str,
                            track_id: str, position: int) -> None:
        
        """Vincula un track a una playlist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO playlist_tracks
                (playlist_id, track_id, position)
                VALUES (?, ?, ?)
            """, (playlist_id, track_id, position))

            conn.commit()
            conn.close()
        return None
    
    # where we at now
    def get_playlist_tracks(self, playlist_id: str) -> list[TrackDict]:
        """Obtiene todos los tracks de una playlist (buscada por id) 
        ordenados por posicion
        List with dict with each dict with keys
        id, name, artists, album, downloaded"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    tracks.id, 
                    tracks.name, 
                    tracks.artists, 
                    albums.name, 
                    tracks.downloaded
                FROM tracks
                JOIN playlist_tracks
                    ON tracks.id = playlist_tracks.track_id
                LEFT JOIN albums
                    ON tracks.album_id = albums.id
                WHERE playlist_tracks.playlist_id = ?
                ORDER BY playlist_tracks.position
            """, (playlist_id, ))

            rows = cursor.fetchall()
            tracks: list[TrackDict] = []
            for row in rows:
                td: TrackDict = {
                    'id': row[0], 
                    'name': row[1],
                    'artists': row[2],
                    'album': row[3] if row[3] else "Unknown", 
                    'downloaded': bool(row[4])
                }
                tracks.append(td)

        return tracks
        
    def get_all_playlist_snapshots(self) -> dict[str, str]:
        """retorna un diccionario {playlist_id: snapshot_id} de todas las playlists"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, snapshot_id FROM playlists")
            snapshots = {row[0]: row[1] for row in cursor.fetchall()}
        
        return snapshots
    
    def get_all_unique_tracks(self) -> list[dict]:
        """Obtiene todos los tracks unicos de la BD"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, artists, album, downloaded, file_path
            FROM tracks
        """)
        
        tracks: list[TrackData] = []
        for row in cursor.fetchall():
            td: TrackData = {
                'id': row[0],
                'name': row[1],
                'artists': row[2],
                'album': row[3],
                'downloaded': row[4],
                'file_path': row[5]
            }
            tracks.append(td)
        conn.close()
        return tracks
    
    def mark_as_downloaded(self, track_id: str, file_path: str) -> None:
        """Marca un track como descargado y guarda su path"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE tracks
                SET downloaded = 1, file_path = ?
                WHERE id = ?
            """, (file_path, track_id))

            conn.commit()
            conn.close()

    def get_statistics(self) -> dict:
        """estadisticas generales de la bdd
        Retorna un diccionario de keys:
        total_tracks,
        downloaded_tracks, 
        total_playlists,
        total_albums, 
        albums_with_covers"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            stats = {}

            #TODO: Eventualmente optimizar las queries, son poco optimas

            # total de tracks
            cursor.execute("SELECT COUNT(*) FROM tracks")
            stats['total_tracks'] = cursor.fetchone()[0]

            # tracks descargados
            cursor.execute("SELECT COUNT(*) FROM tracks WHERE downloaded = 1")
            stats['downloaded_tracks'] = cursor.fetchone()[0]

            # total de playlists
            cursor.execute("SELECT COUNT(*) FROM playlists")
            stats['total_playlists'] = cursor.fetchone()[0]

            # total de albums
            cursor.execute("SELECT COUNT(*) FROM albums")
            stats['total_albums'] = cursor.fetchone()[0]

            # albums con cover
            cursor.execute("SELECT COUNT(*) FROM albums " \
            "WHERE cover_path IS NOT NULL AND cover_path != ''")
            stats['albums_with_covers'] = cursor.fetchone()[0]

            
        return stats

    # Revisar esta funcion!
    def get_all_playlists_summary(self) -> list[dict]:
        """Obtiene lista de playlists con info basica"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(""" 
            SELECT id, name, owner, total_tracks
            FROM playlists
            ORDER BY name
        """)

        playlists = []
        for row in cursor.fetchall():
            playlists.append({
                'id': row[0],
                'name': row[1],
                'owner': row[2],
                'total_tracks': row[3],
            })
        
        conn.close()
        return playlists
    
    def get_all_albums_summary(self) -> list[AlbumSummary]:
        """Obtiene lista de albums con info basica"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, artists, cover_path
                FROM albums
                ORDER BY name
                LIMIT 50
            """)

            albums: list[AlbumSummary] = []
            for row in cursor.fetchall():
                albums.append({
                    'id': row[0],
                    'name': row[1],
                    'artist': row[2],
                    'has_cover': row[3] is not None
                })

            conn.close()
        return albums

    def search_tracks(self, query: str) -> list[dict]:
        """Busca tracks por nombre o por artista"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # funny query lol
            # TODO: Investigar como funciona
            cursor.execute(""" 
                SELECT id, name, artists, downloaded
                FROM tracks
                WHERE name LIKE ? OR artists LIKE ?
                LIMIT 20
            """, (f"%{query}%", f"%{query}%"))

            tracks = []
            for row in cursor.fetchall():
                tracks.append({
                    'id': row[0],
                    'name': row[1],
                    'artists': row[2],
                    'downloaded': bool(row[3])
                })

            conn.close()
        return tracks
#########################################################################

# AI SLOP for testing
if __name__ == '__main__':
    db = Database()
    
    # Crear tracks
    track1 = Track('1', 'Bohemian Rhapsody', ['Queen'], 'A Night at the Opera')
    track2 = Track('2', 'Imagine', ['John Lennon'], 'Imagine')
    
    # Guardar tracks
    db.save_track(track1)
    db.save_track(track2)
    print("✅ Tracks guardados")
    
    # Crear playlist
    playlist = Playlist('p1', 'Rock Classics', 'Juan', 2, 'anckjdsfkjs')
    print(playlist.snapshot_id)
    db.save_playlist(playlist)
    print("✅ Playlist guardada")
    
    # Vincular tracks
    db.link_track_to_playlist('p1', '1', 0)
    db.link_track_to_playlist('p1', '2', 1)
    print("✅ Tracks vinculados")
    
    # Leer tracks de playlist
    tracks = db.get_playlist_tracks('p1')
    print(f"\n📋 Playlist tiene {len(tracks)} tracks:")
    for t in tracks:
        print(f"  - {t['name']} by {t['artists']}")
    
    # Verificar track individual
    track = db.get_track('1')
    print(f"\n🔍 Track recuperado: {track}")

    # TODO: Incluir test de la playlist snapshot id