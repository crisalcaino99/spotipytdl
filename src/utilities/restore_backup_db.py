"""Restore ``music.db.backup`` into the schema the current code expects.

Why this is not a ``cp``:

* The backup predates the ``albums`` table. It stores album *names* in a single
  ``tracks.album`` TEXT column and never recorded album ids at all.
* Its ``playlist_tracks`` has duplicate ``(playlist_id, position)`` pairs, which
  the current ``UNIQUE INDEX`` rejects.
* Some rows carry identifiers or file paths that cannot survive the move.

What this does, in order:

1. copy the backup to the target (the source file is only ever read)
2. renumber ``playlist_tracks.position`` so it is contiguous and unique
3. give the one null-id track a synthetic id
4. add ``tracks.album_id``, rebuild ``albums`` from the album names, and link
5. add ``playlists.last_synced_at``
6. clear ``file_path`` values whose files no longer exist locally
7. create the unique position index and verify with the real ``Database`` API

Album ids are synthesised from the album name (``legacy<sha1 prefix>``) because
the originals are unrecoverable. Consequence: two different albums that share a
name collapse into one row. Covers cannot be restored either -- there are no
cover URLs -- so albums come back with ``cover_url`` NULL until a Spotify sync
or a cover scrape repopulates them.

Run::

    poetry run python src/utilities/restore_backup_db.py
    poetry run python src/utilities/restore_backup_db.py --force
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ALBUMS_DDL = """
CREATE TABLE IF NOT EXISTS albums(
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    artists TEXT NOT NULL,
    cover_url TEXT,
    cover_path TEXT,
    track_count INTEGER DEFAULT 0
)
"""


def album_id_for(name: str) -> str:
    """Stable synthetic id for an album name.

    Case and whitespace are normalised so ``"Nevermind"`` and ``"nevermind "``
    resolve to the same album.
    """
    normalized = " ".join(name.split()).lower()
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()
    return f"legacy{digest[:16]}"


def table_exists(con: sqlite3.Connection, table: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def column_names(con: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in con.execute(f"PRAGMA table_info({table})")}


def count_tracks(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            if not table_exists(con, "tracks"):
                return 0
            return int(con.execute("SELECT COUNT(*) FROM tracks").fetchone()[0])
        finally:
            con.close()
    except sqlite3.Error:
        return 0


def renumber_positions(con: sqlite3.Connection) -> int:
    """Make ``position`` contiguous per playlist, ordered by current position."""
    rows = con.execute(
        "SELECT rowid, playlist_id, position FROM playlist_tracks "
        "ORDER BY playlist_id, position, rowid"
    ).fetchall()

    updates: list[tuple[int, int]] = []
    current_playlist: str | None = None
    counter = 0

    for rowid, playlist_id, position in rows:
        if playlist_id != current_playlist:
            current_playlist, counter = playlist_id, 0
        if position != counter:
            updates.append((counter, rowid))
        counter += 1

    if updates:
        con.executemany("UPDATE playlist_tracks SET position = ? WHERE rowid = ?", updates)

    return len(updates)


def assign_missing_track_ids(con: sqlite3.Connection) -> int:
    rows = con.execute(
        "SELECT rowid FROM tracks WHERE id IS NULL OR TRIM(id) = ''"
    ).fetchall()
    for (rowid,) in rows:
        con.execute(
            "UPDATE tracks SET id = ? WHERE rowid = ?", (f"legacy-track-{rowid}", rowid)
        )
    return len(rows)


def ensure_column(con: sqlite3.Connection, table: str, column: str, ddl: str) -> bool:
    if column in column_names(con, table):
        return False
    con.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
    return True


def build_albums(con: sqlite3.Connection) -> tuple[int, int, int]:
    """Recreate the ``albums`` table from ``tracks.album`` names.

    Returns ``(albums, inserted, linked_tracks)``.
    """
    con.execute(ALBUMS_DDL)

    names = con.execute(
        "SELECT album, COUNT(*) FROM tracks "
        "WHERE album IS NOT NULL AND TRIM(album) <> '' "
        "GROUP BY album"
    ).fetchall()

    # Most frequent artist label per album, used as the album's artist string.
    artist_rows = con.execute(
        "SELECT album, artists, COUNT(*) AS c FROM tracks "
        "WHERE album IS NOT NULL AND TRIM(album) <> '' "
        "GROUP BY album, artists ORDER BY album, c DESC"
    ).fetchall()

    album_artist: dict[str, str] = {}
    for album, artists, _count in artist_rows:
        album_artist.setdefault(album, artists)

    inserted = 0
    linked = 0
    for name, track_count in names:
        aid = album_id_for(name)
        cursor = con.execute(
            "INSERT OR IGNORE INTO albums (id, name, artists, cover_url, cover_path, track_count) "
            "VALUES (?, ?, ?, NULL, NULL, ?)",
            (aid, name, album_artist.get(name, "Unknown"), track_count),
        )
        inserted += cursor.rowcount
        linked += con.execute(
            "UPDATE tracks SET album_id = ? WHERE album = ?", (aid, name)
        ).rowcount

    return len(names), inserted, linked


def clear_dead_downloads(con: sqlite3.Connection, base_dir: Path) -> tuple[int, int]:
    """Reset rows whose recorded file is gone (e.g. paths from another machine).

    Returns ``(cleared, still_present)``.
    """
    rows = con.execute(
        "SELECT rowid, file_path FROM tracks "
        "WHERE file_path IS NOT NULL AND TRIM(file_path) <> ''"
    ).fetchall()

    cleared = 0
    present = 0
    for rowid, raw_path in rows:
        # Old rows were written on Windows; normalise separators before checking.
        candidate = Path(str(raw_path).replace("\\", "/"))
        if not candidate.is_absolute():
            candidate = base_dir / candidate

        if candidate.exists():
            present += 1
        else:
            con.execute(
                "UPDATE tracks SET downloaded = 0, file_path = NULL WHERE rowid = ?",
                (rowid,),
            )
            cleared += 1

    return cleared, present


def migrate(target: Path) -> None:
    con = sqlite3.connect(target)
    try:
        with con:
            if not table_exists(con, "albums"):
                con.execute(ALBUMS_DDL)
                print("  albums table    : created")

            renumbered = renumber_positions(con)
            print(f"  positions       : {renumbered} rows renumbered")

            new_ids = assign_missing_track_ids(con)
            print(f"  missing ids     : {new_ids} track(s) given a synthetic id")

            added = ensure_column(con, "tracks", "album_id", "TEXT")
            print(f"  tracks.album_id : {'added' if added else 'already present'}")

            names, inserted, linked = build_albums(con)
            print(f"  albums          : {names} names -> {inserted} rows, {linked} tracks linked")

            added = ensure_column(con, "playlists", "last_synced_at", "TEXT")
            print(f"  last_synced_at  : {'added' if added else 'already present'}")

            cleared, present = clear_dead_downloads(con, target.parent)
            print(f"  dead file paths : {cleared} cleared, {present} still on disk")

            con.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_playlist_position_unique "
                "ON playlist_tracks (playlist_id, position)"
            )
            print("  unique index    : present")
    finally:
        con.close()


def verify(target: Path) -> bool:
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.database.db_manager import Database  # noqa: PLC0415 - after sys.path setup

    db = Database(str(target))
    stats = db.get_statistics()
    playlists = db.get_all_playlists_summary()

    print("\n=== verification (through the real Database API) ===")
    print(f"  tracks           : {stats['total_tracks']}")
    print(f"  downloaded       : {stats['downloaded_tracks']}")
    print(f"  playlists        : {stats['total_playlists']}")
    print(f"  albums           : {stats['total_albums']}")
    print(f"  albums w/ cover  : {stats['albums_with_covers']}")
    print(f"  playlist summary : {len(playlists)} rows readable")

    if not playlists:
        print("  !! no playlists readable -- something is wrong")
        return False

    blank = sum(1 for p in playlists if not str(p["name"] or "").strip())
    print(f"  blank-name rows  : {blank} (pre-existing data, not a migration problem)")

    ok = True
    named = [p for p in playlists if str(p["name"] or "").strip()]
    for playlist in named[:3]:
        pid = str(playlist["id"])
        tracks = db.get_playlist_tracks(pid)
        unknown = sum(1 for t in tracks if t["album"] == "Unknown")
        contiguous = db.playlist_positions_are_contiguous(pid)
        ok = ok and contiguous
        print(
            f"  '{playlist['name']}': {len(tracks)} tracks, "
            f"{unknown} unknown album(s), positions contiguous={contiguous}"
        )

    sample = db.get_all_unique_tracks()[:1]
    if sample:
        print(f"  sample track     : {sample[0]['name']} / {sample[0]['artists']}")

    return ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    parser.add_argument("--source", default=str(PROJECT_ROOT / "music.db.backup"))
    parser.add_argument("--target", default=str(PROJECT_ROOT / "music.db"))
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite the target even if it already contains tracks",
    )
    args = parser.parse_args(argv)

    source = Path(args.source)
    target = Path(args.target)

    if not source.exists():
        print(f"error: backup not found: {source}")
        return 1
    if source.resolve() == target.resolve():
        print("error: source and target are the same file")
        return 1

    existing = count_tracks(target)
    if existing and not args.force:
        print(
            f"error: {target} already holds {existing} tracks. "
            "Refusing to overwrite without --force."
        )
        return 1

    if target.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safety = target.parent / f"{target.name}.pre-restore-{stamp}"
        shutil.copy2(target, safety)
        print(f"safety copy   : {safety}")

    shutil.copy2(source, target)
    print(f"copied        : {source.name} -> {target.name}")
    print(f"source intact : {source.name} ({count_tracks(source)} tracks)")

    print("\n=== migrating ===")
    migrate(target)

    ok = verify(target)
    print("\ndone" if ok else "\ncompleted with warnings")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
