from __future__ import annotations

import shutil
from pathlib import Path


def delete_file(path: Path) -> None:
    """Elimina un archivo si existe"""
    if path.exists() and path.is_file():
        path.unlink()


def delete_directory(path: Path) -> None:
    """Elimina un directorio completo si existe"""
    if path.exists() and path.is_dir():
        shutil.rmtree(path)
    
def hardcore_reset(
        db_path: Path, 
        downloads_dir: Path | None = None, 
        exports_dir: Path | None = None, 
        covers_dir: Path | None = None, 
) -> None:
    """Elimina todos los artefactos del proyecto"""
    
    delete_file(db_path)

    if downloads_dir: 
        delete_directory(downloads_dir)
    
    if exports_dir:
        delete_directory(exports_dir)

    if covers_dir: 
        delete_directory(covers_dir)
    
    return None





