"""Shared dependencies for the API layer."""
from __future__ import annotations

from src.database.db_manager import Database

_db: Database | None = None


def get_db() -> Database:
    """Return a process-wide :class:`Database` instance.

    ``Database.__init__`` runs ``create_tables``, so instantiating one per
    request would re-check the schema on every call. A single cached instance
    keeps request handling cheap.
    """
    global _db
    if _db is None:
        _db = Database()
    return _db
