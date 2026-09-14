"""
Storage management for Bash Messenger
Handles RAM-based message storage and persistent profile data
"""
import json
import os
from pathlib import Path
from typing import List, Optional, Dict
from collections import deque
from protocol import Message


class MessageBuffer:
    """RAM-based message storage with size limits"""

    def __init__(self, max_size_bytes: int = 265 * 1024 * 1024):
        """
        Initialize message buffer

        Args:
            max_size_bytes: Maximum buffer size (default 265 MB)
        """
        self.messages: deque = deque()
        self.max_size = max_size_bytes
        self.current_size = 0

    def add_message(self, message: Message) -> bool:
        """
        Add message to buffer

        Args:
            message: Message to add

        Returns:
            True if added, False if buffer full
        """
        msg_size = message.get_size()

        # Check if we need to evict old messages (FIFO)
        while self.current_size + msg_size > self.max_size and self.messages:
            evicted = self.messages.popleft()
            self.current_size -= evicted.get_size()

        # Add new message
        if self.current_size + msg_size <= self.max_size:
            self.messages.append(message)
            self.current_size += msg_size
            return True

        return False

    def get_messages(self, limit: Optional[int] = None) -> List[Message]:
        """
        Get messages from buffer

        Args:
            limit: Maximum number of messages to return (most recent)

        Returns:
            List of messages
        """
        if limit:
            return list(self.messages)[-limit:]
        return list(self.messages)

    def clear(self):
        """Clear all messages"""
        self.messages.clear()
        self.current_size = 0

    def get_size_mb(self) -> float:
        """Get current buffer size in MB"""
        return self.current_size / (1024 * 1024)

    def get_usage_percentage(self) -> float:
        """Get buffer usage percentage"""
        return (self.current_size / self.max_size) * 100


class ProfileManager:
    """Manages persistent user profile data"""

    def __init__(self):
        """Initialize profile manager"""
        self.config_dir = Path.home() / '.bash_messenger'
        self.profile_path = self.config_dir / 'profile.json'
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_profile(self) -> Dict:
        """
        Load user profile

        Returns:
            Profile dictionary with username and color
        """
        if not self.profile_path.exists():
            return self._get_default_profile()

        try:
            with open(self.profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
                return profile
        except (json.JSONDecodeError, IOError):
            return self._get_default_profile()

    def save_profile(self, username: str, color: str) -> bool:
        """
        Save user profile

        Args:
            username: User's display name
            color: Hex color code

        Returns:
            True if successful, False otherwise
        """
        profile = {
            'username': username,
            'color': color
        }

        try:
            with open(self.profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2)
            return True
        except IOError:
            return False

    def _get_default_profile(self) -> Dict:
        """Get default profile"""
        return {
            'username': 'User',
            'color': '#00FF00'
        }

    def get_available_colors(self) -> List[Dict[str, str]]:
        """Get list of available colors for user selection"""
        return [
            {'name': 'Green', 'hex': '#00FF00'},
            {'name': 'Blue', 'hex': '#0099FF'},
            {'name': 'Red', 'hex': '#FF5555'},
            {'name': 'Yellow', 'hex': '#FFFF00'},
            {'name': 'Magenta', 'hex': '#FF00FF'},
            {'name': 'Cyan', 'hex': '#00FFFF'},
            {'name': 'Orange', 'hex': '#FF8800'},
            {'name': 'Purple', 'hex': '#AA00FF'},
            {'name': 'Pink', 'hex': '#FF66AA'},
            {'name': 'Lime', 'hex': '#88FF00'},
            {'name': 'Teal', 'hex': '#00AA88'},
            {'name': 'Gold', 'hex': '#FFD700'},
            {'name': 'Coral', 'hex': '#FF7F50'},
            {'name': 'Violet', 'hex': '#9370DB'},
            {'name': 'Turquoise', 'hex': '#40E0D0'},
            {'name': 'White', 'hex': '#FFFFFF'}
        ]


class FileStorage:
    """Handles temporary file storage for received files"""

    def __init__(self):
        """Initialize file storage"""
        self.temp_dir = Path.home() / '.bash_messenger' / 'downloads'
        self._ensure_temp_dir()

    def _ensure_temp_dir(self):
        """Create temp directory if it doesn't exist"""
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, filename: str, data: bytes) -> Optional[Path]:
        """
        Save received file

        Args:
            filename: Name of file
            data: File bytes

        Returns:
            Path to saved file or None if failed
        """
        try:
            # Sanitize filename
            safe_filename = self._sanitize_filename(filename)
            file_path = self.temp_dir / safe_filename

            # Handle duplicate filenames
            counter = 1
            while file_path.exists():
                name, ext = os.path.splitext(safe_filename)
                file_path = self.temp_dir / f"{name}_{counter}{ext}"
                counter += 1

            with open(file_path, 'wb') as f:
                f.write(data)

            return file_path
        except IOError:
            return None

    def _sanitize_filename(self, filename: str) -> str:
        """Remove unsafe characters from filename"""
        # Remove path separators and other unsafe characters
        unsafe_chars = ['/', '\\', '..', '\x00']
        sanitized = filename
        for char in unsafe_chars:
            sanitized = sanitized.replace(char, '_')
        return sanitized
