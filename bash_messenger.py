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
from theme import Theme
from auth import BanManager
from session_history import SessionHistory
from download_manager import DownloadManager, PendingDownload

console = Console()


class BashMessenger:
    """Main application class"""

    def __init__(self):
        """Initialize Bash Messenger"""
        self.profile_manager = ProfileManager()
        self.profile = self.profile_manager.load_profile()
        self.theme = Theme(self.profile.get('theme', 'dark'))
        self.session_manager = None
        self.message_buffer = None  # Will be MessageBuffer or PersistentMessageStorage
        self.file_storage = FileStorage()
        self.file_assembler = FileAssembler()
        self.is_persistent = False  # Session type flag
        self.session_history = SessionHistory()
        self.download_manager = DownloadManager()

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
                await self.show_recent_sessions()
            elif choice == "4":
                self.edit_profile()
            elif choice == "5":
                console.print("\n[yellow]Goodbye![/yellow]")
                break

    def show_banner(self):
        """Display application banner"""
        t = self.theme
        console.print()
        console.print("  ╭" + "─" * 46 + "╮", style=f"{t.get('border')}")
        console.print(f"  │ [bold {t.get('primary')}] BASH MESSENGER[/bold {t.get('primary')}] [{t.get('text_dim')}]v1.0[/{t.get('text_dim')}]" + " " * 23 + "│", style=f"{t.get('border')}")
        console.print(f"  │ [{t.get('text_dim')}]Encrypted P2P Terminal Chat[/{t.get('text_dim')}]" + " " * 11 + "│", style=f"{t.get('border')}")
        console.print("  ╰" + "─" * 46 + "╯", style=f"{t.get('border')}")
        console.print()

    def show_main_menu(self) -> str:
        """Show main menu and get user choice"""
        t = self.theme
        console.print()
        console.print(f"  [{t.get('primary')}]▸[/{t.get('primary')}] [{t.get('menu_header')}]MAIN MENU[/{t.get('menu_header')}]")
        console.print("  " + "─" * 30, style=f"{t.get('border')}")
        console.print()
        console.print(f"  [{t.get('menu_item')}]1[/{t.get('menu_item')}] │ [{t.get('text')}]Create Session[/{t.get('text')}] [{t.get('text_dim')}](Host)[/{t.get('text_dim')}]")
        console.print(f"  [{t.get('menu_item')}]2[/{t.get('menu_item')}] │ [{t.get('text')}]Join Session[/{t.get('text')}] [{t.get('text_dim')}](Client)[/{t.get('text_dim')}]")
        console.print(f"  [{t.get('menu_item')}]3[/{t.get('menu_item')}] │ [{t.get('text')}]Recent Sessions[/{t.get('text')}]")
        console.print(f"  [{t.get('warning')}]4[/{t.get('warning')}] │ [{t.get('text')}]Profile Settings[/{t.get('text')}]")
        console.print(f"  [{t.get('error')}]5[/{t.get('error')}] │ [{t.get('text')}]Exit[/{t.get('text')}]")
        console.print()

        choice = Prompt.ask(f"  [{t.get('input_prompt')}]▸[/{t.get('input_prompt')}]", choices=["1", "2", "3", "4", "5"])
        return choice

    def edit_profile(self):
        """Edit user profile with menu-based selection"""
        while True:
            console.clear()
            t = self.theme
            console.print()
            console.print("  ╭" + "─" * 46 + "╮", style=f"{t.get('border')}")
            console.print(f"  │ [{t.get('primary')}]▸[/{t.get('primary')}] [{t.get('menu_header')}]PROFILE SETTINGS[/{t.get('menu_header')}]" + " " * 22 + "│", style=f"{t.get('border')}")
            console.print("  ╰" + "─" * 46 + "╯", style=f"{t.get('border')}")
            console.print()

            # Show current profile in a box
            current_emoji = self.profile.get('emoji', '👤')
            username_len = len(self.profile['username'])
            theme_name_len = len(t.get_mode_name())

            console.print("  ╭" + "─" * 46 + "╮", style=f"{t.get('border')}")
            console.print(f"  │ [{t.get('text_dim')}]Current Profile:[/{t.get('text_dim')}]" + " " * 29 + "│", style=f"{t.get('border')}")
            console.print(f"  │   {current_emoji} [{self.profile['color']}][bold]{self.profile['username']}[/bold][/{self.profile['color']}]" + " " * (39 - username_len) + "│", style=f"{t.get('border')}")
            console.print(f"  │   [{t.get('text_dim')}]Theme:[/{t.get('text_dim')}] [{t.get('accent')}]{t.get_mode_name()}[/{t.get('accent')}]" + " " * (33 - theme_name_len) + "│", style=f"{t.get('border')}")
            console.print("  ╰" + "─" * 46 + "╯", style=f"{t.get('border')}")
            console.print()

            # Menu options with cleaner style
            console.print(f"  [{t.get('menu_item')}]1[/{t.get('menu_item')}] │ [{t.get('text')}]Change Username[/{t.get('text')}]")
            console.print(f"  [{t.get('menu_item')}]2[/{t.get('menu_item')}] │ [{t.get('text')}]Change Color[/{t.get('text')}]")
            console.print(f"  [{t.get('menu_item')}]3[/{t.get('menu_item')}] │ [{t.get('text')}]Change Emoji[/{t.get('text')}]")
            console.print(f"  [{t.get('menu_item')}]4[/{t.get('menu_item')}] │ [{t.get('text')}]Change Biography[/{t.get('text')}]")
            console.print(f"  [{t.get('menu_item')}]5[/{t.get('menu_item')}] │ [{t.get('text')}]Toggle Theme[/{t.get('text')}] [{t.get('text_dim')}]({t.get_mode_name()})[/{t.get('text_dim')}]")
            console.print(f"  [{t.get('error')}]6[/{t.get('error')}] │ [{t.get('text')}]Back[/{t.get('text')}]")
            console.print()

            choice = Prompt.ask(f"  [{t.get('input_prompt')}]▸[/{t.get('input_prompt')}]", choices=["1", "2", "3", "4", "5", "6"])

            if choice == "1":
                self._change_username()
            elif choice == "2":
                self._change_color()
            elif choice == "3":
                self._change_emoji()
            elif choice == "4":
                self._change_biography()
            elif choice == "5":
                self._toggle_theme()
            elif choice == "6":
                break

    def _change_username(self):
        """Change username"""
        t = self.theme
        console.print()
        new_username = Prompt.ask(f"[{t.get('primary')}]Enter new username[/{t.get('primary')}]", default=self.profile['username'])

        if new_username and new_username != self.profile['username']:
            self.profile['username'] = new_username
            if self.profile_manager.save_profile(
                self.profile['username'],
                self.profile['color'],
                self.profile['emoji'],
                self.theme.get_mode(),
                self.profile.get('bio', '')
            ):
                console.print(f"\n[{t.get('success')}]✓ Username updated to: {new_username}[/{t.get('success')}]")
            else:
                console.print(f"\n[{t.get('error')}]✗ Failed to save profile[/{t.get('error')}]")
        else:
            console.print(f"\n[{t.get('warning')}]Username unchanged[/{t.get('warning')}]")

        Prompt.ask(f"\n[{t.get('text_dim')}]Press Enter to continue[/{t.get('text_dim')}]")

    def _change_color(self):
        """Change color"""
        t = self.theme
        console.print()
        colors = self.profile_manager.get_available_colors()

        table = Table(title="Available Colors", border_style=t.get('border'))
        table.add_column("Number", style=t.get('primary'))
        table.add_column("Color", style=t.get('accent'))
        table.add_column("Preview")

        for i, color in enumerate(colors, 1):
            table.add_row(str(i), color['name'], f"[{color['hex']}]●[/{color['hex']}]")

        console.print(table)

        color_choice = IntPrompt.ask(f"[{t.get('primary')}]Select color number[/{t.get('primary')}]",
                                     choices=[str(i) for i in range(1, len(colors) + 1)])
        new_color = colors[color_choice - 1]['hex']

        self.profile['color'] = new_color
        if self.profile_manager.save_profile(
            self.profile['username'],
            self.profile['color'],
            self.profile['emoji'],
            self.theme.get_mode(),
            self.profile.get('bio', '')
        ):
            console.print(f"\n[{t.get('success')}]✓ Color updated to: {colors[color_choice - 1]['name']}[/{t.get('success')}]")
        else:
            console.print(f"\n[{t.get('error')}]✗ Failed to save profile[/{t.get('error')}]")

        Prompt.ask(f"\n[{t.get('text_dim')}]Press Enter to continue[/{t.get('text_dim')}]")

    def _change_emoji(self):
        """Change emoji"""
        t = self.theme
        console.print()
        emojis = self.profile_manager.get_available_emojis()

        emoji_table = Table(title="Available Emojis", border_style=t.get('border'))
        emoji_table.add_column("Number", style=t.get('primary'))
        emoji_table.add_column("Name", style=t.get('accent'))
        emoji_table.add_column("Emoji", style=t.get('text'))

        for i, emoji_info in enumerate(emojis, 1):
            emoji_table.add_row(str(i), emoji_info['name'], emoji_info['emoji'])

        console.print(emoji_table)

        emoji_choice = IntPrompt.ask(f"[{t.get('primary')}]Select emoji number[/{t.get('primary')}]",
                                     choices=[str(i) for i in range(1, len(emojis) + 1)])
        new_emoji = emojis[emoji_choice - 1]['emoji']

        self.profile['emoji'] = new_emoji
        if self.profile_manager.save_profile(
            self.profile['username'],
            self.profile['color'],
            self.profile['emoji'],
            self.theme.get_mode(),
            self.profile.get('bio', '')
        ):
            console.print(f"\n[{t.get('success')}]✓ Emoji updated to: {new_emoji}[/{t.get('success')}]")
        else:
            console.print(f"\n[{t.get('error')}]✗ Failed to save profile[/{t.get('error')}]")

        Prompt.ask(f"\n[{t.get('text_dim')}]Press Enter to continue[/{t.get('text_dim')}]")

    def _change_biography(self):
        """Change biography"""
        t = self.theme
        console.print()

        current_bio = self.profile.get('bio', '')
        console.print(f"[{t.get('text_dim')}]Current bio ({len(current_bio)}/600 characters):[/{t.get('text_dim')}]")
        if current_bio:
            console.print(f"[{t.get('text')}]{current_bio}[/{t.get('text')}]")
        else:
            console.print(f"[{t.get('text_dim')}]No biography set[/{t.get('text_dim')}]")

        console.print()
        console.print(f"[{t.get('primary')}]Enter new biography (press Enter twice when done, max 600 chars):[/{t.get('primary')}]")

        bio_lines = []
        while True:
            line = input()
            if line == "" and len(bio_lines) > 0 and bio_lines[-1] == "":
                bio_lines.pop()
                break
            bio_lines.append(line)

        new_bio = '\n'.join(bio_lines).strip()

        if len(new_bio) > 600:
            new_bio = new_bio[:600]
            console.print(f"\n[{t.get('warning')}]⚠ Biography truncated to 600 characters[/{t.get('warning')}]")

        self.profile['bio'] = new_bio

        if self.profile_manager.save_profile(
            self.profile['username'],
            self.profile['color'],
            self.profile['emoji'],
            self.theme.get_mode(),
            new_bio
        ):
            console.print(f"\n[{t.get('success')}]✓ Biography updated ({len(new_bio)}/600 characters)[/{t.get('success')}]")
        else:
            console.print(f"\n[{t.get('error')}]✗ Failed to save profile[/{t.get('error')}]")

        Prompt.ask(f"\n[{t.get('text_dim')}]Press Enter to continue[/{t.get('text_dim')}]")

    def _toggle_theme(self):
        """Toggle between dark and light mode"""
        self.theme.switch_mode()
        self.profile['theme'] = self.theme.get_mode()

        if self.profile_manager.save_profile(
            self.profile['username'],
            self.profile['color'],
            self.profile['emoji'],
            self.theme.get_mode(),
            self.profile.get('bio', '')
        ):
            t = self.theme
            console.print(f"\n[{t.get('success')}]✓ Theme changed to: {t.get_mode_name()}[/{t.get('success')}]")
        else:
            console.print(f"\n[{t.get('error')}]✗ Failed to save theme[/{t.get('error')}]")

        Prompt.ask(f"\n[{t.get('text_dim')}]Press Enter to continue[/{t.get('text_dim')}]")

    async def create_session(self):
        """Create new session as host"""
        console.clear()
        t = self.theme
        console.print()
        console.print("  ╭" + "─" * 46 + "╮", style=f"{t.get('border')}")
        console.print(f"  │ [{t.get('primary')}]▸[/{t.get('primary')}] [{t.get('menu_header')}]CREATE SESSION[/{t.get('menu_header')}]" + " " * 24 + "│", style=f"{t.get('border')}")
        console.print("  ╰" + "─" * 46 + "╯", style=f"{t.get('border')}")
        console.print()

        # Ask for session type
        console.print(f"  [{t.get('primary')}]Session Type:[/{t.get('primary')}]")
        console.print()
        console.print(f"  [{t.get('menu_item')}]1[/{t.get('menu_item')}] │ [{t.get('text')}]Temporary[/{t.get('text')}] [{t.get('text_dim')}](RAM, 265MB, ends when closed)[/{t.get('text_dim')}]")
        console.print(f"  [{t.get('menu_item')}]2[/{t.get('menu_item')}] │ [{t.get('text')}]Persistent[/{t.get('text')}] [{t.get('text_dim')}](Disk, 2GB, saves history)[/{t.get('text_dim')}]")
        console.print()

        session_type = Prompt.ask(f"  [{t.get('input_prompt')}]▸[/{t.get('input_prompt')}]", choices=["1", "2"], default="1")

        if session_type == "2":
            self.is_persistent = True
            console.print(f"\n  [{t.get('success')}]✓[/{t.get('success')}] [{t.get('text')}]Persistent session (2GB storage)[/{t.get('text')}]")
        else:
            self.is_persistent = False
            console.print(f"\n  [{t.get('success')}]✓[/{t.get('success')}] [{t.get('text')}]Temporary session (265MB RAM)[/{t.get('text')}]")

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

        console.print(f"  [{t.get('text_dim')}]Your IP:[/{t.get('text_dim')}] [{t.get('warning')}]{local_ip}[/{t.get('warning')}]")
        console.print(f"  [{t.get('text_dim')}]Note: Clients need your public IP for internet connections[/{t.get('text_dim')}]")
        console.print()

        # Generate keys
        session_key = generate_session_key(local_ip)
        connection_key = generate_connection_key()
        connection_key_hash = hash_connection_key(connection_key)

        # Show session info with modern styling
        console.print("  ╭" + "─" * 46 + "╮", style=f"{t.get('success')}")
        console.print(f"  │ [{t.get('menu_header')}]SESSION CREDENTIALS[/{t.get('menu_header')}]" + " " * 26 + "│", style=f"{t.get('success')}")
        console.print("  ├" + "─" * 46 + "┤", style=f"{t.get('success')}")
        console.print(f"  │  [{t.get('text_dim')}]Session Key:[/{t.get('text_dim')}]     [{t.get('warning')}][bold]{session_key}[/bold][/{t.get('warning')}]" + " " * (25 - len(session_key)) + "│", style=f"{t.get('success')}")
        console.print(f"  │  [{t.get('text_dim')}]Connection Key:[/{t.get('text_dim')}]  [{t.get('warning')}][bold]{connection_key}[/bold][/{t.get('warning')}]" + " " * (21 - len(connection_key)) + "│", style=f"{t.get('success')}")
        console.print("  │" + " " * 46 + "│", style=f"{t.get('success')}")
        console.print(f"  │  [{t.get('text_dim')}]Share these with clients[/{t.get('text_dim')}]" + " " * 21 + "│", style=f"{t.get('success')}")
        console.print("  ╰" + "─" * 46 + "╯", style=f"{t.get('success')}")
        console.print()

        port = IntPrompt.ask(f"  [{t.get('input_prompt')}]Port[/{t.get('input_prompt')}]", default=5555)

        # Initialize session
        self.session_manager = SessionManager(session_key, connection_key, is_host=True)
        # Host username is always "HOST" (not shown to others)
        self.host_username = "HOST"

        # Initialize storage based on session type
        if self.is_persistent:
            self.message_buffer = PersistentMessageStorage(session_key, max_size_bytes=2 * 1024 * 1024 * 1024)
            console.print(f"  [{t.get('text_dim')}]Storage: ~/.bash_messenger/sessions/{session_key}.db[/{t.get('text_dim')}]")
        else:
            self.message_buffer = MessageBuffer(max_size_bytes=265 * 1024 * 1024)
            console.print(f"  [{t.get('text_dim')}]Storage: RAM only (temporary)[/{t.get('text_dim')}]")

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
            console.print(f"\n  [{t.get('success')}]✓[/{t.get('success')}] [{t.get('text')}]Session started on port {port}[/{t.get('text')}]")
            console.print(f"  [{t.get('text_dim')}]Waiting for clients...[/{t.get('text_dim')}]")
            console.print()

            # Save session to history
            self.session_history.save_session(
                session_key, local_ip, port, connection_key,
                self.profile['username'], is_host=True
            )

            # Start chat interface
            await self.run_chat_interface()

        except Exception as e:
            console.print(f"\n  [{t.get('error')}]✗ Failed to start session: {e}[/{t.get('error')}]")
            Prompt.ask(f"\n  [{t.get('text_dim')}]Press Enter to continue[/{t.get('text_dim')}]")

    async def join_session(self):
        """Join existing session as client"""
        console.clear()
        t = self.theme
        console.print()
        console.print("  ╭" + "─" * 46 + "╮", style=f"{t.get('border')}")
        console.print(f"  │ [{t.get('primary')}]▸[/{t.get('primary')}] [{t.get('menu_header')}]JOIN SESSION[/{t.get('menu_header')}]" + " " * 26 + "│", style=f"{t.get('border')}")
        console.print("  ╰" + "─" * 46 + "╯", style=f"{t.get('border')}")
        console.print()

        # Get session details
        session_key = Prompt.ask(f"  [{t.get('input_prompt')}]Session Key (6 digits)[/{t.get('input_prompt')}]").upper()
        host_ip = Prompt.ask(f"  [{t.get('input_prompt')}]Host IP Address[/{t.get('input_prompt')}]")
        port = IntPrompt.ask(f"  [{t.get('input_prompt')}]Port[/{t.get('input_prompt')}]", default=5555)
        connection_key = Prompt.ask(f"  [{t.get('input_prompt')}]Connection Key (8 digits)[/{t.get('input_prompt')}]", password=True)

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

            # Save session to history
            self.session_history.save_session(
                session_key, host_ip, port, connection_key,
                self.profile['username'], is_host=False
            )

            await self.run_chat_interface()
        else:
            console.print("\n[red]✗ Connection failed[/red]")
            Prompt.ask("\nPress Enter to continue")

    async def show_recent_sessions(self):
        """Show and reconnect to recent sessions"""
        console.clear()
        t = self.theme
        console.print()
        console.print("  ╭" + "─" * 46 + "╮", style=f"{t.get('border')}")
        console.print(f"  │ [{t.get('primary')}]▸[/{t.get('primary')}] [{t.get('menu_header')}]RECENT SESSIONS[/{t.get('menu_header')}]" + " " * 23 + "│", style=f"{t.get('border')}")
        console.print("  ╰" + "─" * 46 + "╯", style=f"{t.get('border')}")
        console.print()

        history = self.session_history.load_history()

        if not history:
            console.print(f"  [{t.get('text_dim')}]No recent sessions found[/{t.get('text_dim')}]")
            console.print()
            Prompt.ask(f"  [{t.get('text_dim')}]Press Enter to continue[/{t.get('text_dim')}]")
            return

        # Display sessions
        console.print(f"  [{t.get('text_dim')}]Recent sessions:[/{t.get('text_dim')}]")
        console.print()

        for i, session in enumerate(history, 1):
            role = "HOST" if session['is_host'] else "CLIENT"
            role_color = t.get('success') if session['is_host'] else t.get('primary')

            console.print(f"  [{t.get('menu_item')}]{i}[/{t.get('menu_item')}] │ [{t.get('text')}]{session['session_key']}[/{t.get('text')}] [{role_color}]{role}[/{role_color}]")
            console.print(f"      [{t.get('text_dim')}]IP: {session['host_ip']}:{session['port']} | User: {session['username']}[/{t.get('text_dim')}]")
            console.print()

        console.print(f"  [{t.get('error')}]0[/{t.get('error')}] │ [{t.get('text')}]Back[/{t.get('text')}]")
        console.print()

        choices = [str(i) for i in range(0, len(history) + 1)]
        choice = Prompt.ask(f"  [{t.get('input_prompt')}]Select session to reconnect[/{t.get('input_prompt')}]", choices=choices)

        if choice == "0":
            return

        # Reconnect to selected session
        session = history[int(choice) - 1]
        await self.reconnect_to_session(session)

    async def reconnect_to_session(self, session: dict):
        """Reconnect to a saved session"""
        t = self.theme
        console.print()
        console.print(f"  [{t.get('text')}]Reconnecting to session {session['session_key']}...[/{t.get('text')}]")
        console.print()

        # Initialize session
        self.session_manager = SessionManager(session['session_key'], session['connection_key'], is_host=session['is_host'])

        if session['is_host']:
            # Reconnect as host
            self.is_persistent = False
            self.message_buffer = MessageBuffer(max_size_bytes=265 * 1024 * 1024)
            self.host_username = "HOST"

            self.network = Host(
                session['session_key'],
                hash_connection_key(session['connection_key']),
                self.on_message_received,
                self.on_user_joined,
                self.on_user_left
            )

            encryption = MessageEncryption(session['session_key'], session['connection_key'])
            self.network.set_encryption(encryption)

            try:
                await self.network.start('0.0.0.0', session['port'])
                console.print(f"  [{t.get('success')}]✓[/{t.get('success')}] [{t.get('text')}]Session started on port {session['port']}[/{t.get('text')}]")
                console.print(f"  [{t.get('text_dim')}]Waiting for clients...[/{t.get('text_dim')}]")
                console.print()
                await self.run_chat_interface()
            except Exception as e:
                console.print(f"  [{t.get('error')}]✗ Failed to start session: {e}[/{t.get('error')}]")
                Prompt.ask(f"\n  [{t.get('text_dim')}]Press Enter to continue[/{t.get('text_dim')}]")
        else:
            # Reconnect as client
            self.message_buffer = MessageBuffer()
            self.is_persistent = False

            self.network = Client(
                session['session_key'],
                session['connection_key'],
                self.profile['username'],
                self.profile['color'],
                self.on_message_received,
                self.on_connected,
                self.on_disconnected
            )

            if await self.network.connect(session['host_ip'], session['port']):
                console.print(f"  [{t.get('success')}]✓ Connected successfully![/{t.get('success')}]")
                console.print()
                await self.run_chat_interface()
            else:
                console.print(f"  [{t.get('error')}]✗ Connection failed[/{t.get('error')}]")
                Prompt.ask(f"\n  [{t.get('text_dim')}]Press Enter to continue[/{t.get('text_dim')}]")

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
            console.print("[dim]All Commands: /quit, /users, /file <path>, /downloads, /clear, /memory[/dim]\n")
        else:
            console.print("[dim]Commands: /quit, /users, /file <path>, /downloads, /clear, /memory[/dim]\n")
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
                    emoji = self.profile.get('emoji', '👤')
                    message = Message(
                        MessageType.TEXT,
                        sender_name,
                        user_input,
                        self.profile['color'],
                        metadata={'emoji': emoji}
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

        elif cmd == '/memory':
            self.show_memory_usage()

        elif cmd == '/downloads':
            self.show_downloads()

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
        console.print(f"║  [bold white]Connected Users: {client_count}/50[/bold white]" + " " * (23 - len(str(client_count))) + "║", style="bold cyan")
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

    def show_memory_usage(self):
        """Show storage/memory usage statistics"""
        t = self.theme
        console.print()

        if self.is_persistent:
            # Persistent storage
            used_mb = self.message_buffer.get_size_mb()
            max_mb = 2048  # 2GB
            percentage = (used_mb / max_mb) * 100
            storage_type = "Persistent (Disk)"

            console.print("  ╭" + "─" * 46 + "╮", style=f"{t.get('border')}")
            console.print(f"  │ [{t.get('primary')}]STORAGE USAGE[/{t.get('primary')}]" + " " * 29 + "│", style=f"{t.get('border')}")
            console.print("  ├" + "─" * 46 + "┤", style=f"{t.get('border')}")
            console.print(f"  │  [{t.get('text_dim')}]Type:[/{t.get('text_dim')}] [{t.get('text')}]{storage_type}[/{t.get('text')}]" + " " * (33 - len(storage_type)) + "│", style=f"{t.get('border')}")
            console.print(f"  │  [{t.get('text_dim')}]Used:[/{t.get('text_dim')}] [{t.get('warning')}]{used_mb:.2f} MB[/{t.get('warning')}] [{t.get('text_dim')}]/ {max_mb} MB[/{t.get('text_dim')}]" + " " * (18 - len(f"{used_mb:.2f}")) + "│", style=f"{t.get('border')}")

            # Progress bar
            bar_width = 30
            filled = int((percentage / 100) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)

            if percentage < 50:
                bar_color = t.get('success')
            elif percentage < 80:
                bar_color = t.get('warning')
            else:
                bar_color = t.get('error')

            console.print(f"  │  [{bar_color}]{bar}[/{bar_color}] [{t.get('text')}]{percentage:.1f}%[/{t.get('text')}]" + " " * (8 - len(f"{percentage:.1f}")) + "│", style=f"{t.get('border')}")
            console.print("  ╰" + "─" * 46 + "╯", style=f"{t.get('border')}")
        else:
            # Temporary storage (RAM)
            used_mb = self.message_buffer.get_size_mb()
            max_mb = 265  # 265MB
            percentage = (used_mb / max_mb) * 100
            storage_type = "Temporary (RAM)"

            console.print("  ╭" + "─" * 46 + "╮", style=f"{t.get('border')}")
            console.print(f"  │ [{t.get('primary')}]MEMORY USAGE[/{t.get('primary')}]" + " " * 30 + "│", style=f"{t.get('border')}")
            console.print("  ├" + "─" * 46 + "┤", style=f"{t.get('border')}")
            console.print(f"  │  [{t.get('text_dim')}]Type:[/{t.get('text_dim')}] [{t.get('text')}]{storage_type}[/{t.get('text')}]" + " " * (33 - len(storage_type)) + "│", style=f"{t.get('border')}")
            console.print(f"  │  [{t.get('text_dim')}]Used:[/{t.get('text_dim')}] [{t.get('warning')}]{used_mb:.2f} MB[/{t.get('warning')}] [{t.get('text_dim')}]/ {max_mb} MB[/{t.get('text_dim')}]" + " " * (19 - len(f"{used_mb:.2f}")) + "│", style=f"{t.get('border')}")

            # Progress bar
            bar_width = 30
            filled = int((percentage / 100) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)

            if percentage < 50:
                bar_color = t.get('success')
            elif percentage < 80:
                bar_color = t.get('warning')
            else:
                bar_color = t.get('error')

            console.print(f"  │  [{bar_color}]{bar}[/{bar_color}] [{t.get('text')}]{percentage:.1f}%[/{t.get('text')}]" + " " * (8 - len(f"{percentage:.1f}")) + "│", style=f"{t.get('border')}")
            console.print("  ╰" + "─" * 46 + "╯", style=f"{t.get('border')}")

        console.print()

    def show_downloads(self):
        """Show pending downloads and allow user to download them"""
        t = self.theme
        console.print()

        pending = self.download_manager.get_pending_downloads()

        if not pending:
            console.print(f"  [{t.get('text_dim')}]No pending downloads[/{t.get('text_dim')}]")
            console.print()
            return

        console.print("  ╭" + "─" * 58 + "╮", style=f"{t.get('border')}")
        console.print(f"  │ [{t.get('primary')}]PENDING DOWNLOADS[/{t.get('primary')}]" + " " * 40 + "│", style=f"{t.get('border')}")
        console.print("  ├" + "─" * 58 + "┤", style=f"{t.get('border')}")

        for i, download in enumerate(pending, 1):
            filename_display = download.filename[:35] + "..." if len(download.filename) > 35 else download.filename
            size_display = download.get_size_display()
            sender_display = download.sender[:15] + "..." if len(download.sender) > 15 else download.sender

            console.print(f"  │  [{t.get('menu_item')}]{i}[/{t.get('menu_item')}] │ [{t.get('text')}]{filename_display}[/{t.get('text')}]" + " " * (40 - len(filename_display)) + "│", style=f"{t.get('border')}")
            console.print(f"  │      [{t.get('text_dim')}]From: {sender_display} | Size: {size_display}[/{t.get('text_dim')}]" + " " * (35 - len(sender_display) - len(size_display)) + "│", style=f"{t.get('border')}")

            if i < len(pending):
                console.print("  │" + " " * 58 + "│", style=f"{t.get('border')}")

        console.print("  ╰" + "─" * 58 + "╯", style=f"{t.get('border')}")
        console.print()

        console.print(f"  [{t.get('text_dim')}]Enter file number to download, or press Enter to cancel[/{t.get('text_dim')}]")
        choice = Prompt.ask(f"  [{t.get('input_prompt')}]▸[/{t.get('input_prompt')}]", default="")

        if choice and choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(pending):
                download = pending[idx]
                self.download_file(download)
            else:
                console.print(f"  [{t.get('error')}]Invalid selection[/{t.get('error')}]")

        console.print()

    def download_file(self, download):
        """Download a file with progress bar"""
        t = self.theme
        console.print()
        console.print(f"  [{t.get('text')}]Downloading: {download.filename}[/{t.get('text')}]")

        # Request file from storage
        file_data = self.file_storage.get_file(download.file_id)

        if not file_data:
            console.print(f"  [{t.get('error')}]✗ File not found[/{t.get('error')}]")
            self.download_manager.remove_pending(download.file_id)
            return

        # Mark as downloading
        self.download_manager.start_download(download.file_id)

        # Simulate progress bar (in real implementation, this would be during transfer)
        from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            DownloadColumn(),
            TransferSpeedColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"  [{t.get('primary')}]Downloading...[/{t.get('primary')}]", total=len(file_data))

            # Simulate chunked download
            chunk_size = 1024 * 100  # 100KB chunks
            downloaded = 0

            for i in range(0, len(file_data), chunk_size):
                chunk = file_data[i:i + chunk_size]
                downloaded += len(chunk)
                self.download_manager.update_progress(download.file_id, downloaded)
                progress.update(task, completed=downloaded)

        # Save file
        filepath = self.download_manager.complete_download(download.file_id, file_data)

        if filepath:
            console.print(f"  [{t.get('success')}]✓ Downloaded to: {filepath}[/{t.get('success')}]")
        else:
            console.print(f"  [{t.get('error')}]✗ Failed to save file[/{t.get('error')}]")

        console.print()

    async def send_file(self, file_path: str):
        """Send file to session with progress bar"""
        try:
            # Clean up file path (remove quotes if dragged and dropped)
            file_path = file_path.strip().strip('"').strip("'")

            path = Path(file_path)
            if not path.exists():
                console.print(f"[red]File not found: {file_path}[/red]")
                return

            if not path.is_file():
                console.print(f"[red]Not a file: {file_path}[/red]")
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

            t = self.theme
            console.print(f"[{t.get('primary')}]📤 Sending file: {path.name} ({PendingDownload._format_size(len(file_data))})[/{t.get('primary')}]")

            # Send chunks with progress bar
            from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn

            chunks = list(file_msg.get_chunks())

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                DownloadColumn(),
                TransferSpeedColumn(),
                console=console
            ) as progress:
                task = progress.add_task(f"  [{t.get('primary')}]Uploading...[/{t.get('primary')}]", total=len(chunks))

                for i, chunk_message in enumerate(chunks):
                    if isinstance(self.network, Host):
                        await self.network.send_message(chunk_message)
                    elif isinstance(self.network, Client):
                        await self.network.send_message(chunk_message)

                    progress.update(task, completed=i + 1)

            console.print(f"[{t.get('success')}]✓ File sent: {path.name}[/{t.get('success')}]")

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
                filesize = len(file_data)
                sender = message.sender

                # Save to file storage temporarily
                file_id = self.file_storage.save_file(filename, file_data)

                if file_id:
                    # Add to pending downloads
                    self.download_manager.add_pending_download(
                        file_id, filename, filesize, sender
                    )

                    t = self.theme
                    console.print(f"[{t.get('success')}]📥 File received: {filename} ({PendingDownload._format_size(filesize)}) from {sender}[/{t.get('success')}]")
                    console.print(f"[{t.get('text_dim')}]   Use /downloads to save to your Downloads folder[/{t.get('text_dim')}]")
                else:
                    console.print(f"[red]✗ Failed to receive file: {filename}[/red]")

        elif message.type == MessageType.SYSTEM:
            console.print(f"[bold yellow]» [/bold yellow][dim]{message.content}[/dim]")

    def display_message(self, message: Message):
        """Display message in terminal"""
        timestamp = self.format_timestamp(message.timestamp)

        # Get emoji from metadata or use default
        emoji = message.metadata.get('emoji', '👤')

        username_colored = f"{emoji} [{message.color}][bold]{message.sender}[/bold][/{message.color}]"
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
