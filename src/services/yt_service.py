import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yt_dlp
import os
import re

class YoutubeService:
    def __init__(self, download_dir: str = 'downloads'):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
    
    def search_and_download(self, track_name: str, artist: str) -> str|None:
        # Implementar algoritmo que verifique que fue la cancion solicitada
        # Como hacemos eso lol
        downloaded_file = None

        # definimos d como un evento
        # TODO: Completar esta funcion
        def progress_hook(d: dict):
            nonlocal downloaded_file
            if d['status'] == 'finished':
                base_name = d['filename'].rsplit('.', 1)[0]
                downloaded_file = base_name + '.mp3'
            
        
        search_query = f"{artist} {track_name}"
        ydl_opts = {
            'format': 'bestaudio/best',
            'ffmpeg_location': r'C:\Users\Vicente\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin',
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
            print('ERROR {e}')
            return None

if __name__ == '__main__':
    service = YoutubeService()
    file_path = service.search_and_download('Bohemian Rhapsody', 'Queen')

    if file_path:
        print(f"Descargado {file_path}")
        print(f'Existe {Path(file_path).exists()}')
    else: 
        print("Fallo la descarga")
    
