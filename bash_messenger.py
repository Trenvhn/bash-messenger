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
from storage import MessageBuffer, ProfileManager, FileStorage, PersistentMessageStorage
from profile_picture import ProfilePicture
from auth import BanManager

console = Console()


class BashMessenger:
    """Main application class"""

    def __init__(self):
        """Initialize Bash Messenger"""
        self.profile_manager = ProfileManager()
        self.profile = self.profile_manager.load_profile()
        self.session_manager = None
        self.message_buffer = None  # Will be MessageBuffer or PersistentMessageStorage
        self.file_storage = FileStorage()
        self.file_assembler = FileAssembler()
        self.is_persistent = False  # Session type flag

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
        console.print()
        console.print("=" * 50, style="bold blue")
        console.print("           BASH MESSENGER v1.0", style="bold cyan")
        console.print("     Encrypted P2P Terminal Messenger", style="dim cyan")
        console.print("=" * 50, style="bold blue")
        console.print()

    def show_main_menu(self) -> str:
        """Show main menu and get user choice"""
        console.print()
        console.print("[bold cyan]╔══════════════════════════════════╗[/bold cyan]")
        console.print("[bold cyan]║[/bold cyan]         [bold white]MAIN MENU[/bold white]              [bold cyan]║[/bold cyan]")
        console.print("[bold cyan]╚══════════════════════════════════╝[/bold cyan]")
        console.print()
        console.print("[bold green]1.[/bold green] [white]Create Session[/white] [dim](Host)[/dim]")
        console.print("[bold green]2.[/bold green] [white]Join Session[/white] [dim](Client)[/dim]")
        console.print("[bold yellow]3.[/bold yellow] [white]Profile Settings[/white]")
        console.print("[bold red]4.[/bold red] [white]Exit[/white]")
        console.print()

        choice = Prompt.ask("[bold cyan]Select option[/bold cyan]", choices=["1", "2", "3", "4"])
        return choice

    def edit_profile(self):
        """Edit user profile"""
        console.clear()
        console.print()
        console.print("╔" + "═" * 48 + "╗", style="bold cyan")
        console.print("║" + " " * 14 + "[bold white]PROFILE SETTINGS[/bold white]" + " " * 16 + "║", style="bold cyan")
        console.print("╚" + "═" * 48 + "╝", style="bold cyan")
        console.print()

        # Show current profile
        console.print(f"[bold cyan]Current Username:[/bold cyan] [green]{self.profile['username']}[/green]")
        console.print(f"[bold cyan]Current Color:[/bold cyan]    [{self.profile['color']}]●[/{self.profile['color']}] {self.profile['color']}")

        # Show current avatar
        current_avatar_key = self.profile.get('avatar', 'default')
        console.print(f"[bold cyan]Current Avatar:[/bold cyan]   {current_avatar_key}\n")

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

        # Show avatar options
        console.print()
        avatars = ProfilePicture.get_avatar_list()
        avatar_table = Table(title="Available Avatars")
        avatar_table.add_column("Number", style="cyan")
        avatar_table.add_column("Name", style="magenta")
        avatar_table.add_column("Preview")

        for i, avatar in enumerate(avatars, 1):
            mini = ProfilePicture.get_avatar_mini(avatar['key'])
            avatar_table.add_row(str(i), avatar['name'], mini)

        console.print(avatar_table)

        avatar_choice = IntPrompt.ask("Select avatar number",
                                     choices=[str(i) for i in range(1, len(avatars) + 1)])
        new_avatar = avatars[avatar_choice - 1]['key']

        # Show preview
        console.print()
        console.print("╔" + "═" * 48 + "╗", style="bold green")
        console.print("║" + " " * 18 + "[bold white]PREVIEW[/bold white]" + " " * 20 + "║", style="bold green")
        console.print("╚" + "═" * 48 + "╝", style="bold green")
        console.print()

        avatar_lines = ProfilePicture.get_avatar(new_avatar)
        for line in avatar_lines:
            console.print(f"[{new_color}]{line}[/{new_color}]")

        console.print()
        console.print(f"[{new_color}]●[/{new_color}] [{new_color}][bold]{new_username}[/bold][/{new_color}]")
        console.print()

        # Save profile
        self.profile['username'] = new_username
        self.profile['color'] = new_color
        self.profile['avatar'] = new_avatar

        if self.profile_manager.save_profile(new_username, new_color, new_avatar):
            console.print("\n[green]✓ Profile saved successfully![/green]")
        else:
            console.print("\n[red]✗ Failed to save profile[/red]")

        Prompt.ask("\nPress Enter to continue")
        console.clear()

    async def create_session(self):
        """Create new session as host"""
        console.clear()
        console.print()
        console.print("╔" + "═" * 48 + "╗", style="bold cyan")
        console.print("║" + " " * 15 + "[bold white]CREATE SESSION[/bold white]" + " " * 15 + "║", style="bold cyan")
        console.print("╚" + "═" * 48 + "╝", style="bold cyan")
        console.print()

        # Ask for session type
        console.print("[bold cyan]Select Session Type:[/bold cyan]\n")
        console.print("[bold green]1.[/bold green] [white]Temporary Session[/white] [dim](RAM only, 265MB, ends when closed)[/dim]")
        console.print("[bold yellow]2.[/bold yellow] [white]Persistent Session[/white] [dim](Disk storage, 2GB, saves history)[/dim]\n")

        session_type = Prompt.ask("[bold cyan]Session type[/bold cyan]", choices=["1", "2"], default="1")

        if session_type == "2":
            self.is_persistent = True
            console.print("\n[green]✓ Persistent session selected (2GB storage)[/green]")
        else:
            self.is_persistent = False
            console.print("\n[green]✓ Temporary session selected (265MB RAM)[/green]")

        console.print()

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

        # Show session info with better styling
        console.print()
        console.print("╔" + "═" * 48 + "╗", style="bold green")
        console.print("║" + " " * 12 + "[bold white]SESSION INFORMATION[/bold white]" + " " * 15 + "║", style="bold green")
        console.print("╠" + "═" * 48 + "╣", style="bold green")
        console.print(f"║  [bold cyan]Session Key:[/bold cyan]      [bold yellow]{session_key}[/bold yellow]" + " " * (26 - len(session_key)) + "║", style="bold green")
        console.print(f"║  [bold cyan]Connection Key:[/bold cyan]   [bold yellow]{connection_key}[/bold yellow]" + " " * (22 - len(connection_key)) + "║", style="bold green")
        console.print("║" + " " * 48 + "║", style="bold green")
        console.print("║  [dim]Share these keys with clients[/dim]          ║", style="bold green")
        console.print("╚" + "═" * 48 + "╝", style="bold green")
        console.print()

        port = IntPrompt.ask("\nEnter port to listen on", default=5555)

        # Initialize session
        self.session_manager = SessionManager(session_key, connection_key, is_host=True)
        # Host username is always "HOST" (not shown to others)
        self.host_username = "HOST"

        # Initialize storage based on session type
        if self.is_persistent:
            self.message_buffer = PersistentMessageStorage(session_key, max_size_bytes=2 * 1024 * 1024 * 1024)
            console.print(f"[dim]Storage: ~/.bash_messenger/sessions/{session_key}.db[/dim]")
        else:
            self.message_buffer = MessageBuffer(max_size_bytes=265 * 1024 * 1024)
            console.print(f"[dim]Storage: RAM only (temporary)[/dim]")

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
        console.print()
        console.print("╔" + "═" * 48 + "╗", style="bold cyan")
        console.print("║" + " " * 16 + "[bold white]JOIN SESSION[/bold white]" + " " * 16 + "║", style="bold cyan")
        console.print("╚" + "═" * 48 + "╝", style="bold cyan")
        console.print()

        # Get session details
        session_key = Prompt.ask("Enter Session Key (6 digits)").upper()
        host_ip = Prompt.ask("Enter Host IP address")
        port = IntPrompt.ask("Enter Port", default=5555)
        connection_key = Prompt.ask("Enter Connection Key (8 digits)", password=True)

        # Initialize session
        self.session_manager = SessionManager(session_key, connection_key, is_host=False)

        # For clients, always use RAM buffer (they don't control storage)
        self.message_buffer = MessageBuffer()
        self.is_persistent = False

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

        console.print()
        console.print("╔" + "═" * 58 + "╗", style="bold green")
        console.print("║" + " " * 15 + "[bold white]CHAT SESSION STARTED[/bold white]" + " " * 15 + "    ║", style="bold green")
        console.print("╚" + "═" * 58 + "╝", style="bold green")
        console.print()
        console.print("[dim cyan]Type your message and press Enter to send[/dim cyan]")
        if isinstance(self.network, Host):
            console.print("[dim yellow]Host Commands: /kick <user>, /ban <user>[/dim yellow]")
            console.print("[dim]All Commands: /quit, /users, /file <path>, /clear[/dim]\n")
        else:
            console.print("[dim]Commands: /quit, /users, /file <path>, /clear[/dim]\n")
        console.print("─" * 60, style="blue")
        console.print()

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
                    # Use HOST as sender name if hosting
                    sender_name = self.host_username if isinstance(self.network, Host) else self.profile['username']
                    message = Message(
                        MessageType.TEXT,
                        sender_name,
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

        elif cmd == '/kick':
            if not isinstance(self.network, Host):
                console.print("[red]Only the host can kick users[/red]")
            elif len(parts) < 2:
                console.print("[red]Usage: /kick <username>[/red]")
            else:
                await self.kick_user(parts[1])

        elif cmd == '/ban':
            if not isinstance(self.network, Host):
                console.print("[red]Only the host can ban users[/red]")
            elif len(parts) < 2:
                console.print("[red]Usage: /ban <username>[/red]")
            else:
                await self.ban_user(parts[1])

        elif cmd == '/history':
            if self.is_persistent:
                limit = 50
                if len(parts) > 1:
                    try:
                        limit = int(parts[1])
                    except:
                        pass
                self.show_history(limit)
            else:
                console.print("[yellow]History only available in persistent sessions[/yellow]")

        else:
            console.print(f"[red]Unknown command: {cmd}[/red]")

    def show_users(self):
        """Show connected users (excluding HOST)"""
        info = self.session_manager.get_session_info()
        # Count only clients, not host
        client_count = len([u for u in self.session_manager.connected_users if u['username'] != 'HOST'])

        console.print()
        console.print("╔" + "═" * 38 + "╗", style="bold cyan")
        console.print(f"║  [bold white]Connected Users: {client_count}/4[/bold white]" + " " * (23 - len(str(client_count))) + "║", style="bold cyan")
        console.print("╠" + "═" * 38 + "╣", style="bold cyan")

        for user_info in self.session_manager.connected_users:
            # Don't show HOST in the list
            if user_info['username'] != 'HOST':
                username = user_info['username']
                console.print(f"║  [green]●[/green] [white]{username}[/white]" + " " * (33 - len(username)) + "║", style="bold cyan")

        if client_count == 0:
            console.print("║  [dim]No users connected yet[/dim]          ║", style="bold cyan")

        console.print("╚" + "═" * 38 + "╝", style="bold cyan")
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
            sender_name = self.host_username if isinstance(self.network, Host) else self.profile['username']
            file_msg = FileMessage(path.name, file_data,
                                  sender_name, self.profile['color'])

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
            console.print(f"[bold yellow]» [/bold yellow][dim]{message.content}[/dim]")

    def display_message(self, message: Message):
        """Display message in terminal"""
        timestamp = self.format_timestamp(message.timestamp)

        # Get avatar mini icon (emoji fallback for non-Unicode support)
        avatar_mini = "●"  # Default bullet point

        username_colored = f"[{message.color}]{avatar_mini}[/{message.color}] [{message.color}][bold]{message.sender}[/bold][/{message.color}]"
        console.print(f"[dim cyan]{timestamp}[/dim cyan] {username_colored} [white]{message.content}[/white]")

    def format_timestamp(self, timestamp: float) -> str:
        """Format timestamp for display"""
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%H:%M:%S")

    async def on_user_joined(self, username: str, color: str):
        """Handle user join event (clients only, not host)"""
        self.session_manager.add_user(username)
        message = Message(MessageType.SYSTEM, "System",
                         f"→ {username} joined the session", "#00FF00")
        await self.on_message_received(message)

    async def on_user_left(self, username: str):
        """Handle user leave event"""
        self.session_manager.remove_user(username)
        message = Message(MessageType.SYSTEM, "System",
                         f"← {username} left the session", "#FF5555")
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
    async def kick_user(self, username: str):
        """Kick user from session (host only)"""
        if username == "HOST":
            console.print("[red]Cannot kick the host[/red]")
            return

        if username not in self.network.clients:
            console.print(f"[red]User '{username}' not found[/red]")
            return

        # Send kick notification
        kick_msg = Message(
            MessageType.SYSTEM,
            "System",
            f"{username} has been kicked by HOST",
            "#FF0000"
        )
        await self.network.broadcast_message(kick_msg)
        await self.on_message_received(kick_msg)

        # Close connection
        writer = self.network.clients[username]
        writer.close()
        await writer.wait_closed()

        console.print(f"[yellow]✓ Kicked {username}[/yellow]")

    async def ban_user(self, username: str):
        """Ban user from session (host only)"""
        if username == "HOST":
            console.print("[red]Cannot ban the host[/red]")
            return

        if username not in self.network.clients:
            console.print(f"[red]User '{username}' not found[/red]")
            return

        # Get user IP
        user_info = self.network.client_info[username]
        user_ip = user_info['address'][0]

        # Ban IP permanently for this session
        self.network.ban_manager.ban_ip(user_ip)

        # Send ban notification
        ban_msg = Message(
            MessageType.SYSTEM,
            "System",
            f"{username} has been banned by HOST",
            "#FF0000"
        )
        await self.network.broadcast_message(ban_msg)
        await self.on_message_received(ban_msg)

        # Close connection
        writer = self.network.clients[username]
        writer.close()
        await writer.wait_closed()

        console.print(f"[red]✓ Banned {username} (IP: {user_ip})[/red]")
    def show_history(self, limit: int = 50):
        """Show message history (persistent sessions only)"""
        if not self.is_persistent:
            console.print("[yellow]History not available in temporary sessions[/yellow]")
            return

        messages = self.message_buffer.get_messages(limit=limit)
        total = self.message_buffer.get_message_count()

        console.print()
        console.print("╔" + "═" * 58 + "╗", style="bold cyan")
        console.print(f"║  [bold white]MESSAGE HISTORY[/bold white] [dim](showing {len(messages)} of {total})[/dim]" + " " * (33 - len(str(len(messages))) - len(str(total))) + "║", style="bold cyan")
        console.print("╚" + "═" * 58 + "╝", style="bold cyan")
        console.print()

        if not messages:
            console.print("[dim]No messages in history[/dim]\n")
            return

        for msg in messages:
            self.display_message(msg)

        console.print()
        console.print(f"[dim]Storage: {self.message_buffer.get_size_mb():.2f} MB / 2048 MB ({self.message_buffer.get_usage_percentage():.1f}%)[/dim]\n")
