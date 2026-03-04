import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .schemas.spotify_types import TrackDict

console = Console()

def show_menu() -> None:
    """Muestra el menu principal"""
    console.clear()

    console.print("\n")
    console.print(
        " [bold magenta] Spotify playlist downloader [/bold magenta]",
        justify="center"
    )
    console.print("\n")

    table = Table(
        show_header=True, 
        header_style="bold cyan"
    )

    table.add_column("Option", style="cyan", width=8)
    table.add_column("Action", style="white")

    table.add_row("1", "sync playlists from spotify")
    table.add_row("2", "download pending tracks")
    table.add_row("3", "scrape album covers")
    table.add_row("4", "show something")
    table.add_row("5", "quit")
    table.add_row("6", "see playlists")

    console.print(table)
    console.print("\n")


def option_sync_spotify() -> None:
    """Opcion 1: Sincronizar con spotify"""
    console.print("\n [bold green] Syncing with spotify.. [/bold green]")

    from main import sync_spotify_to_database
    sync_spotify_to_database()

    console.print(Panel('playlists exitosamente sincronizadas',
                        border_style='green',
                        title='success'))
    
    console.input('\n [dim] Press enter to continue [/dim]')
    return None

def show_playlist_tracks(playlist: dict) -> None: 
    """Muestra los tracks de una playlist con navegacion.
    Es auxiliar de (option_browse_interactive)"""
    
    import questionary

    from database.db_manager import Database

    db = Database()

    while True:
        console.clear()
        console.print(f"\n[bold green] {playlist['name']}[/bold green]")
        console.print(f"[dim] by {playlist['owner']}[/dim]\n")
        
        # careful in here
        tracks = db.get_playlist_tracks(playlist['id'])

        if not tracks:
            console.print('[yellow] No tracks in this playlist [/yellow]')
            console.input('\n Press Enter...')
            return
        
        menu_options = []

        for i, t in enumerate(tracks, 1):
            # something is wrong in 
            status = "check" if t.get('downloaded') else " (not downloaded yet) "
            label = f"{i:3d}. {status} {t['name']} - {t['artists']}"
            menu_options.append(label)
            
        menu_options.append("<- Back")

        answer = questionary.select(
            f"Tracks in {playlist['name']}:",
            choices = menu_options, 
            style=questionary.Style([
                ('selected', 'bg:green fg:black'),
                ('pointer', 'fg:green bold'),
            ])
        ).ask()

        if answer is None or "Back" in answer:
            break
        
        selected_index = menu_options.index(answer)

        if selected_index < len(tracks):
            show_track_details(tracks[selected_index])

    return None

def show_track_details(track: TrackDict) -> None:
    """Muestra detalles de un track"""
    console.clear()
    console.print("\n[bold cyan] Track Details [/bold cyan]\n")

    from textwrap import dedent
    info = dedent(f"""
    [bold]Name:[/bold] {track.get('name', 'Unknown')}
    [bold]Artists:[/bold] {track.get('artists', 'Unknown')}
    [bold]Album:[/bold] {track.get('album', 'Unknown')}
    [bold]Downloaded:[/bold]{'Yes' if track.get('downloaded') else 'No'}
    """)

    from rich.panel import Panel
    console.print(Panel(info.strip(), border_style='cyan'))
    console.input('\n [dim] Press Enter to continue...[/dim]')

    return None

def option_browse_playlists_interactive() -> None:
    """Navegar playlists con flechas. Opcion"""
    import questionary

    from database.db_manager import Database

    db = Database()

    # Bucle de GUI
    while True:
        console.clear()
        console.print("\n [bold cyan] Browse Playlists [/bold cyan] \n")

        playlists = db.get_all_playlists_summary()
        
        if not playlists:
            console.print("[yellow]No playlists found[/yellow]")
            console.input("\nPress Enter...")
            return None
        
        menu_options = [f"{p['name']} ({p['total_tracks']} tracks)" for p in playlists]
        menu_options.append("<- Back")

        answer = questionary.select(
            "Select a playlist:",
            choices = menu_options, 
            style = questionary.Style([
                ('selected', 'bg:green fg:black'),
                ('pointer', 'fg:cyan bold'),
                ('highlighted', 'fg:#00ffff bold')
            ])
        ).ask()

        if answer is None or answer == '<- Back':
            break

        selected_index = menu_options.index(answer)

        if selected_index is None or selected_index == len(playlists):
            break

        selected_playlist = playlists[selected_index]
        show_playlist_tracks(selected_playlist)
        return None


def option_show_statistics() -> None:
    """Opcion 4: Mostrar estadisticas"""
    from database.db_manager import Database

    console.print("\n [bold cyan] Database Statistics [/bold cyan]\n")

    db = Database()
    stats = db.get_statistics()

    # Crear tabla de estadisticas
    table = Table(show_header=False, border_style='cyan')
    table.add_column("Metric", style="yellow")
    table.add_column("Value", style='green', justify='right')

    table.add_row('total tracks', str(stats['total_tracks']))
    table.add_row('downloaded tracks', str(stats['downloaded_tracks']))
    table.add_row('total playlists', str(stats['total_playlists']))
    table.add_row('total albums', str(stats['total_albums']))
    table.add_row('albums with covers', str(stats['albums_with_covers']))
    
    console.print(table)
    console.input('\n [dim] Press Enter to continue [/dim]')
    return None

def main() -> None:
    #TODO: Corrections to do and stuff
    """Loop principal del CLI"""
    while True:
        show_menu()
        choice = console.input(
            "[bold yellow] > Select option: [/bold yellow]" 
        )
        if choice == '1':
            option_sync_spotify()
            return None
        elif choice == '2':
            from download_tracks import download_all_tracks  # noqa: F401
            # not implemented yet
            # TODO: implementar la funcion download_all_tracks()
            # pero con un int que se seleccione
            console.input('\n Press Enter...')
            return None
        elif choice == '4':
            option_show_statistics()
            return None
        elif choice == '6':
            option_browse_playlists_interactive()
            return None
        else:
            console.print("Not yet!")
            console.input("\n Press Enter...")
            return None
    return None
if __name__ == "__main__":
    main()
