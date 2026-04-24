from typing import Optional

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.database.db_manager import Database

app = FastAPI(
    title="Spotipyt",
    description="A simple local service to download your playlists",
    version="1.0.0"
)
app.mount("/static", StaticFiles(directory="static"), name="static")

db = Database()

# TODO: Add routes
@app.get("/api/playlists")
def get_playlists():
    # TODO: Hacer que este endpoint retorne una wea util sipo kjfkjsjdsakj
    return db.get_all_playlist_snapshots()


@app.get("/api/tracks")
def get_tracks():
    return db.get_all_unique_tracks()

