import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import Database


def reset_database() -> None:
    # TODO: escribir el .env
    db_path = 'music.db'

    if os.path.exists(db_path):
        os.remove(db_path)
        print(f" Base de datos eliminada {db_path}")
    
    Database()
    print('Base de datos creada con nuevo esquema')

# test
if __name__ == '__main__':
    confirm = input(' Esto borrara todos los datos: Continuar? (yes/no)')
    if confirm.lower() == 'yes':
        reset_database()
    else:
        print('cancelado')
        

