"""
Main application for Bash Messenger
Terminal-based encrypted P2P messenger
"""
import asyncio
import sys
import os
from pathlib import Path

# Rich imports for terminal UI
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich import box

# Local imports
from session import SessionManager, generate_session_key, generate_connection_key
from encryption import MessageEncryption, hash_connection_key
from protocol import Message, MessageType, FileMessage, FileAssembler
from network import Host, Client
from storage import MessageBuffer, ProfileManager, FileStorage
from auth import BanManager

console = Console()


class BashMessenger:
    """Main application class"""

    def __init__(self):
        """Initialize Bash Messenger"""
        self.profile_manager = ProfileManager()
        self.profile = self.profile_manager.load_profile()
        self.session_manager = None
        self.message_buffer = MessageBuffer()
        self.file_storage = FileStorage()
        self.file_assembler = FileAssembler()

        self.network = None  # Will be Host or Client
        self.running = False
        self.typing_users = set()

    async def start(self):
        """Start application"""
        console.clear()
        self.show_banner()

        while True:
            choice = self.show_main_menu()

            if choice == "1":
                await self.create_session()
            elif choice == "2":
                await self.join_session()
            elif choice == "3":
                self.edit_profile()
            elif choice == "4":
                console.print("\n[yellow]Goodbye![/yellow]")
                break

    def show_banner(self):
        """Display application banner"""
        banner = """
========================================
      BASH MESSENGER v1.0
  Encrypted P2P Terminal Messenger
========================================
        """
        console.print(banner, style="bold cyan")

    def show_main_menu(self) -> str:
        """Show main menu and get user choice"""
        console.print("\n[bold cyan]Main Menu[/bold cyan]")
        console.print("1. Create Session (Host)")
        console.print("2. Join Session (Client)")
        console.print("3. Profile Settings")
        console.print("4. Exit")

        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4"])
        return choice

    def edit_profile(self):
        """Edit user profile"""
        console.clear()
        console.print("[bold cyan]Profile Settings[/bold cyan]\n")

        # Show current profile
        console.print(f"Current Username: [green]{self.profile['username']}[/green]")
        console.print(f"Current Color: [{self.profile['color']}]●[/{self.profile['color']}] {self.profile['color']}\n")

        # Edit username
        new_username = Prompt.ask("Enter new username (or press Enter to keep current)",
                                 default=self.profile['username'])

        # Show color options
        colors = self.profile_manager.get_available_colors()
        table = Table(title="Available Colors")
        table.add_column("Number", style="cyan")
        table.add_column("Color", style="magenta")
        table.add_column("Preview")

        for i, color in enumerate(colors, 1):
            table.add_row(str(i), color['name'], f"[{color['hex']}]●[/{color['hex']}]")

        console.print(table)

        color_choice = IntPrompt.ask("Select color number",
                                     choices=[str(i) for i in range(1, len(colors) + 1)])
        new_color = colors[color_choice - 1]['hex']

        # Save profile
        self.profile['username'] = new_username
        self.profile['color'] = new_color

        if self.profile_manager.save_profile(new_username, new_color):
            console.print("\n[green]✓ Profile saved successfully![/green]")
        else:
            console.print("\n[red]✗ Failed to save profile[/red]")

        Prompt.ask("\nPress Enter to continue")
        console.clear()

    async def create_session(self):
        """Create new session as host"""
        console.clear()
        console.print("[bold cyan]Create Session[/bold cyan]\n")

        # Get local IP
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = "127.0.0.1"

        console.print(f"Your IP: [yellow]{local_ip}[/yellow]")
        console.print("[dim]Note: Clients need your public IP if connecting over internet[/dim]\n")

        # Generate keys
        session_key = generate_session_key(local_ip)
        connection_key = generate_connection_key()
        connection_key_hash = hash_connection_key(connection_key)

        # Show session info
        panel = Panel(
            f"[bold]Session Key:[/bold] [yellow]{session_key}[/yellow]\n"
            f"[bold]Connection Key:[/bold] [yellow]{connection_key}[/yellow]\n\n"
            f"[dim]Share these with clients to allow them to connect[/dim]",
            title="Session Information",
            border_style="green"
        )
        console.print(panel)

        port = IntPrompt.ask("\nEnter port to listen on", default=5555)

        # Initialize session
        self.session_manager = SessionManager(session_key, connection_key, is_host=True)
        self.session_manager.add_user(self.profile['username'])

        # Create host
        self.network = Host(
            session_key, connection_key_hash,
            self.on_message_received,
            self.on_user_joined,
            self.on_user_left
        )

        # Initialize encryption
        encryption = MessageEncryption(session_key, connection_key)
        self.network.set_encryption(encryption)

        try:
            await self.network.start('0.0.0.0', port)
            console.print(f"\n[green]✓ Session started on port {port}[/green]")
            console.print("[dim]Waiting for clients to connect...[/dim]\n")

            # Start chat interface
            await self.run_chat_interface()

        except Exception as e:
            console.print(f"\n[red]✗ Failed to start session: {e}[/red]")
            Prompt.ask("\nPress Enter to continue")

    async def join_session(self):
        """Join existing session as client"""
        console.clear()
        console.print("[bold cyan]Join Session[/bold cyan]\n")

        # Get session details
        session_key = Prompt.ask("Enter Session Key (6 digits)").upper()
        host_ip = Prompt.ask("Enter Host IP address")
        port = IntPrompt.ask("Enter Port", default=5555)
        connection_key = Prompt.ask("Enter Connection Key (8 digits)", password=True)

        # Initialize session
        self.session_manager = SessionManager(session_key, connection_key, is_host=False)

        # Create client
        self.network = Client(
            session_key, connection_key,
            self.profile['username'], self.profile['color'],
            self.on_message_received,
            self.on_connected,
            self.on_disconnected
        )

        console.print("\n[yellow]Connecting...[/yellow]")

        if await self.network.connect(host_ip, port):
            console.print("[green]✓ Connected successfully![/green]\n")
            await self.run_chat_interface()
        else:
            console.print("\n[red]✗ Connection failed[/red]")
            Prompt.ask("\nPress Enter to continue")

    async def run_chat_interface(self):
        """Run chat interface"""
        self.running = True

        console.print("[bold green]Chat Session Started[/bold green]")
        console.print("[dim]Type your message and press Enter to send[/dim]")
        console.print("[dim]Commands: /quit, /users, /file <path>, /clear[/dim]\n")
        console.print("─" * 60 + "\n")

        # Start input handler
        input_task = asyncio.create_task(self.handle_user_input())

        try:
            await input_task
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            if isinstance(self.network, Host):
                await self.network.stop()
            elif isinstance(self.network, Client):
                await self.network.disconnect()

    async def handle_user_input(self):
        """Handle user input in chat"""
        loop = asyncio.get_event_loop()

        while self.running:
            try:
                # Get input (non-blocking)
                user_input = await loop.run_in_executor(None, input, "")

                if not user_input.strip():
                    continue

                # Handle commands
                if user_input.startswith('/'):
                    await self.handle_command(user_input)
                else:
                    # Send message
                    message = Message(
                        MessageType.TEXT,
                        self.profile['username'],
                        user_input,
                        self.profile['color']
                    )

                    if isinstance(self.network, Host):
                        await self.network.send_message(message)
                    elif isinstance(self.network, Client):
                        await self.network.send_message(message)
                        # Don't display here - will receive from host broadcast

            except EOFError:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    async def handle_command(self, command: str):
        """Handle chat commands"""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()

        if cmd == '/quit':
            self.running = False
            console.print("\n[yellow]Leaving session...[/yellow]")

        elif cmd == '/users':
            self.show_users()

        elif cmd == '/clear':
            console.clear()

        elif cmd == '/file':
            if len(parts) < 2:
                console.print("[red]Usage: /file <path>[/red]")
            else:
                await self.send_file(parts[1])

        else:
            console.print(f"[red]Unknown command: {cmd}[/red]")

    def show_users(self):
        """Show connected users"""
        info = self.session_manager.get_session_info()
        console.print(f"\n[cyan]Connected Users: {info['connected_users']}/{info['max_users']}[/cyan]")
        for user_info in self.session_manager.connected_users:
            console.print(f"  • {user_info['username']}")
        console.print()

    async def send_file(self, file_path: str):
        """Send file to session"""
        try:
            path = Path(file_path)
            if not path.exists():
                console.print(f"[red]File not found: {file_path}[/red]")
                return

            # Read file
            with open(path, 'rb') as f:
                file_data = f.read()

            # Check size
            if not self.session_manager.can_accept_data(len(file_data)):
                console.print("[red]File too large for session limit[/red]")
                return

            # Create file message
            file_msg = FileMessage(path.name, file_data,
                                  self.profile['username'], self.profile['color'])

            console.print(f"[yellow]Sending file: {path.name} ({len(file_data)} bytes)[/yellow]")

            # Send chunks
            for chunk_message in file_msg.get_chunks():
                if isinstance(self.network, Host):
                    await self.network.send_message(chunk_message)
                elif isinstance(self.network, Client):
                    await self.network.send_message(chunk_message)

            console.print(f"[green]✓ File sent: {path.name}[/green]")

        except Exception as e:
            console.print(f"[red]Error sending file: {e}[/red]")

    async def on_message_received(self, message: Message):
        """Handle received message"""
        # Add to buffer
        self.message_buffer.add_message(message)
        self.session_manager.message_count += 1
        self.session_manager.add_data(message.get_size())

        # Handle different message types
        if message.type == MessageType.TEXT:
            self.display_message(message)

        elif message.type == MessageType.FILE_CHUNK:
            # Assemble file
            file_data = self.file_assembler.add_chunk(message)
            if file_data:
                filename = message.metadata['filename']
                saved_path = self.file_storage.save_file(filename, file_data)
                if saved_path:
                    console.print(f"[green]✓ File received: {filename} -> {saved_path}[/green]")
                else:
                    console.print(f"[red]✗ Failed to save file: {filename}[/red]")

        elif message.type == MessageType.SYSTEM:
            console.print(f"[dim]{message.content}[/dim]")

    def display_message(self, message: Message):
        """Display message in terminal"""
        timestamp = self.format_timestamp(message.timestamp)
        username_colored = f"[{message.color}]{message.sender}[/{message.color}]"
        console.print(f"[dim]{timestamp}[/dim] {username_colored}: {message.content}")

    def format_timestamp(self, timestamp: float) -> str:
        """Format timestamp for display"""
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%H:%M:%S")

    async def on_user_joined(self, username: str, color: str):
        """Handle user join event"""
        self.session_manager.add_user(username)
        message = Message(MessageType.SYSTEM, "System",
                         f"{username} joined the session", "#888888")
        await self.on_message_received(message)

    async def on_user_left(self, username: str):
        """Handle user leave event"""
        self.session_manager.remove_user(username)
        message = Message(MessageType.SYSTEM, "System",
                         f"{username} left the session", "#888888")
        await self.on_message_received(message)

    async def on_connected(self):
        """Handle successful connection (client)"""
        self.session_manager.add_user(self.profile['username'])

    async def on_disconnected(self):
        """Handle disconnection (client)"""
        console.print("\n[red]Disconnected from session[/red]")
        self.running = False


def main():
    """Main entry point"""
    try:
        app = BashMessenger()
        asyncio.run(app.start())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
