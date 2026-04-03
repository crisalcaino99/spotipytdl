import sys
from pathlib import Path

from database.db_manager import Database
from services.playlist_exp import export_playlist_bundle

sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from schemas.spotify_types import TrackDict

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

    try:
        sync_spotify_to_database()
        console.print(Panel('playlists exitosamente sincronizadas',
                        border_style='green',
                        title='success'))
    
        console.input('\n [dim] Press enter to continue [/dim]')
        return None
    
    except Exception as e:
        console.print(f"Error: {e} ha ocurrido. Vuelve a intentar")
        return None
    
def export_playlist_interactive(
        db: Database, 
        playlist_id: str, 
        playlist_name: str,
) -> None:
    tracks = db.get_playlist_tracks(playlist_id)

    if not tracks: 
        console.print('[red]Playlist vacia o sin tracks asociados.[/red]')
        console.input('\n[dim]Press Enter to continue...[/dim]')
        return
    
    export_root = Path('exports') / playlist_name
    
    # TODO: fix in here
    try:
        playlist_path = export_playlist_bundle(
            playlist_name = playlist_name, 
            tracks = tracks, 
            export_root = export_root,
        )
    
    except Exception as e:
        console.print(
            Panel(
                f"Error exporting playlist:\n{e}",
                title = 'Error',
                border_style='red',
            )
        )
        console.input("\n[dim] Press Enter to continue...[/dim]")
        return
    
    console.print(
        Panel(
            f"Playlist exported succesfully:\n{playlist_path}",
            title = "Success",
            border_style='green'
        )
    )
    console.input("\n[dim]Press Enter to continue...[/dim]")


def show_playlist_tracks(playlist: dict[str, Any]) -> None: 
    """Muestra los tracks de una playlist con navegacion.
    Es auxiliar de (option_browse_interactive)"""
    import os

    import questionary
    console.print(os.getcwd())
    from rich.panel import Panel

    from src.database.db_manager import Database
    from src.services.spotify_service import generate_sp_service
    from src.services.sync_service import get_playlist_status

    # testing in progress
    db = Database('music.db')
    
    while True:
        console.clear()
        console.print(f"\n[bold green] {playlist['name']}[/bold green]")
        console.print(f"[dim] by {playlist['owner']}[/dim]\n")
        
        # careful in here
        # this is calling itself each time. It would be far better if you could store it
        # from the beginning and then consulting it or something like it.

        service = generate_sp_service()
        local_snapshot, remote_snapshot, status = get_playlist_status(
            db = db, 
            spotify = service,
            playlist_id = playlist['id']
        )

        status_styles = {
            "created": "bold blue",
            "updated": "bold red",
            "unchanged": "bold green"
        }

        status_messages = {
            "created": "Playlist not synced yet",
            "updated": "Changes detected since last sync",
            "unchanged": "Playlist is up to date"
        }

        status_style = status_styles.get(status, "bold yellow")
        status_messages = status_messages.get(status, "Unknown status")

        header = (
            f"[bold green]{playlist['name']}[/bold green]\n"
            f"[dim]by {playlist['owner']}[/dim]\n"
            f"[dim]Tracks: {playlist.get('total_tracks', '?')}[/dim]\n"
            f"[dim]Last synced: {playlist.get('last_synced_at') or 'Never'}[/dim]\n\n"
            f"[cyan]Local snapshot:[/cyan] {local_snapshot or 'Not synced'}\n"
            f"[cyan]Remote snapshot:[/cyan] {remote_snapshot}\n\n"
            f"[{status_style}]Status: {status.upper()}[/{status_style}]\n"
            f"[dim]{status_messages}[/dim]"
        )

        console.print(Panel(header, title = "Playlist Info", border_style="cyan"))
        console.print()

        tracks = db.get_playlist_tracks(playlist['id'])

        if not tracks:
            console.print('[yellow] No tracks in this playlist [/yellow]')
            console.input('\n Press Enter...')
            return
        
        menu_options: list[str] = []

        for t in tracks:
            status = "✓" if t.get('downloaded') else "(not downloaded yet)"
            artists_str = ", ".join(t['artists'])
            position = t.get('position', '?')
            label = f"{position:>3}. {status} {t['name']} - {artists_str}"
            menu_options.append(label)

        
        menu_options.append(" ↓ Download pending tracks")
        menu_options.append("[Export this playlist]")
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

        if answer == "[Export this playlist]":
            export_playlist_interactive(db=db, playlist_id = str(playlist.get('id')),
                                        playlist_name = str(playlist.get('name'))) 
            tracks = db.get_playlist_tracks(str(playlist.get('id')))
            continue


        if answer == ' ↓ Download pending tracks':
            from src.download_tracks import download_pending_tracks_from_playlist
            
            console.clear()
            console.print(
                f"\n[bold cyan] Downloading pending tracks from {playlist['name']}\
                    [/bold cyan]\n"
            )

            stats = download_pending_tracks_from_playlist(playlist['id'])

            from rich.panel import Panel

            console.print(
                Panel(
                    f"Downloaded: {stats['downloaded']}\n"
                    f"Failed: {stats['failed']}\n"
                    f"Skipped: {stats['skipped']}",
                    title = 'Download summary',
                    border_style='green' if stats['failed'] == 0 else 'yellow',
                )
            )

            console.input("\n[dim] Press Enter to continue...[/dim]")
            continue

        selected_index = menu_options.index(answer)

        if selected_index < len(tracks):
            show_track_details(tracks[selected_index])

def show_track_details(track: TrackDict) -> None:
    """Muestra detalles de un track"""
    console.clear()
    console.print("\n[bold cyan] Track Details [/bold cyan]\n")

    from textwrap import dedent

    from rich.panel import Panel

    from src.download_tracks import download_single_track

    artists_value = track.get("artists", [])
    artists_str = ', '.join(artists_value) or 'Unknown'

    info = dedent(f"""
    [bold]Name:[/bold] {track.get('name', 'Unknown')}
    [bold]Artists:[/bold] {artists_str}
    [bold]Album:[/bold] {track.get('album', 'Unknown')}
    [bold]Downloaded:[/bold]{'Yes' if track.get('downloaded') else 'No'}
    """)

    console.print(Panel(info.strip(), border_style='cyan'))

    console.print('\n[bold yellow]Actions[/bold yellow]')
    if track.get("downloaded"):
        console.print("1. Re download track")
    else:
        console.print("1. Download track")
    console.print("2. Back")

    choice = console.input("\n[bold yellow]> Select option: [/bold yellow]").strip()

    if choice == '1':
        try:
            file_path = download_single_track(track)

            if file_path:
                track['downloaded'] = True
                track['file_path'] = file_path

                console.print(
                    Panel(
                        f"Downloaded successfully:\n{file_path}",
                        title="Sucess",
                        border_style='green'
                    )
                )

            else:
                console.print(
                    Panel(
                        'Download failed',
                        title = 'Error',
                        border_style='red'
                    )
                )
        
        except Exception as e:
            console.print(
                Panel(
                    f"Error downloading track:\n{e}",
                    title='Error',
                    border_style='red'
                )
            )
            
        console.input('\n [dim] Press Enter to continue...[/dim]')

    elif choice == '2':
        return

    else:
        console.print("[red]Invalid option[/red]")
        console.input("\n[dim]Press Enter to continue...[/dim]")
    
    return None

def option_browse_playlists_interactive() -> None:
    """Navegar playlists con flechas. Opcion"""
    import questionary

    # FIX THIS
    # TODO: FIX THIS PLS PLS PLS PLS
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

        if selected_index is None or selected_index == len(playlists): # type: ignore
            break

        selected_playlist = playlists[selected_index]
        show_playlist_tracks(selected_playlist)
        
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

        elif choice == '2':
            from download_tracks import download_all_tracks  # type: ignore # noqa: F401
            # not implemented yet
            # TODO: implementar la funcion download_all_tracks()
            # pero con un int que se seleccione
            console.input('\n Press Enter...')
            
        elif choice == '4':
            option_show_statistics()

        elif choice == '5':
            break
            
        elif choice == '6':
            option_browse_playlists_interactive()
            
        else:
            console.print("Not yet!")
            console.input("\n Press Enter...")
            
    
if __name__ == "__main__":
    main()
