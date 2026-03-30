import sys
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).parent.parent))


import re

import yt_dlp


def sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '', name)


class Downloader:
    def __init__(self, download_dir: Path, ffmpeg_location: str | None) -> None:
        self.download_dir = download_dir
        self.ffmpeg_location = ffmpeg_location
    
    def search_and_download(self, track_name: str, artist: str) -> str | None :
        downloaded_mp3: Path | None = None

        def progress_hook(d: dict[str, Any]) -> None:
            nonlocal downloaded_mp3

            if d.get("status") != "finished":
                return
            
            filename = d.get("filename")
            if not filename:
                return
            
            downloaded_mp3 = Path(filename).with_suffix(".mp3")
        
        search_query = f"{artist} {track_name}"
        safe_name = sanitize_filename(f"{artist} {track_name}") # ignore
        search_query = re.sub(r"\s+", " ", search_query).strip()

        ydl_opts: Mapping[str, Any] = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": str(self.download_dir / "f{safe_name}.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [progress_hook],
        }

        if self.ffmpeg_location:
            ydl_opts['ffmpeg_location'] = self.ffmpeg_location
            
        try: 
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: # type: ignore

                info = ydl.extract_info(f"ytsearch1:{search_query}", download=True) #type: ignore
                if "entries" in info:
                    entries: Any = info.get("entries") or []
                    if entries:
                        info = entries[0]
                
                if downloaded_mp3 is None:
                    prepared = ydl.prepare_filename(info) 
                    downloaded_mp3 = Path(prepared).with_suffix(".mp3")

        except Exception as e:
            print(f"Error {e}")
            return None
        
        if downloaded_mp3 is not None and downloaded_mp3.exists(): # type: ignore
            return str(downloaded_mp3)
        
        # Potencial error al retornar None, quizas debiese retornar un Exception o algo
        # de ese estilo.
        return None

    
"""
class YoutubeService:
    def __init__(self, download_dir: str = 'downloads') -> None:
        self.download_dir = Path(download_dir)
        self.ffmpeg_location = ffm
    
    def search_and_download(self, track_name: str, artist: str) -> str|None:
        # Implementar algoritmo que verifique que fue la cancion solicitada
        # Como hacemos eso lol
        downloaded_file = None

        # definimos d como un evento
        # TODO: Completar esta funcion

        def progress_hook(d: dict[str, str]) -> None: # type: ignore
            nonlocal downloaded_file
            if d['status'] == 'finished':
                base_name = d['filename'].rsplit('.', 1)[0]
                downloaded_file = base_name + '.mp3'
            
            return None
        
        search_query = f"{artist} {track_name}"
        ydl_opts : dict[str, Any] = {
            'format': 'bestaudio/best',

            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                # TODO: modificar esto
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': str(self.download_dir / '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'default_search' : 'ytsearch1:',
            'progress_hooks': [progress_hook],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=True)
                video_title = info['title']
                safe_title = re.sub(r'[<>:"/\\|?*]', '', video_title)
                # como guarda ydl el archivo lol
                file_path = self.download_dir / f"{safe_title}.mp3"
                
                if downloaded_file and Path(downloaded_file).exists():
                    print('Descargado')
                    return downloaded_file
                
                print('No se pudo obtener el path del archivo')
                return None
            
        except Exception as e:
            print(f'ERROR {e}')
            return None

if __name__ == '__main__':
    service = YoutubeService()
    file_path = service.search_and_download('Bohemian Rhapsody', 'Queen')

    if file_path:
        print(f"Descargado {file_path}")
        print(f'Existe {Path(file_path).exists()}')
    else: 
        print("Fallo la descarga")
    
"""