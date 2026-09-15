"""
Storage management for Bash Messenger
Handles RAM-based message storage, disk-based persistent storage, and profile data
"""
import json
import os
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict
from collections import deque
from protocol import Message
from datetime import datetime


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


class PersistentMessageStorage:
    """Disk-based persistent message storage using SQLite"""

    def __init__(self, session_key: str, max_size_bytes: int = 2 * 1024 * 1024 * 1024):
        """
        Initialize persistent storage

        Args:
            session_key: Session identifier
            max_size_bytes: Maximum storage size (default 2 GB)
        """
        self.session_key = session_key
        self.max_size = max_size_bytes
        self.storage_dir = Path.home() / '.bash_messenger' / 'sessions'
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.storage_dir / f"{session_key}.db"
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                sender TEXT NOT NULL,
                content TEXT NOT NULL,
                color TEXT NOT NULL,
                type TEXT NOT NULL,
                metadata TEXT,
                size INTEGER NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_info (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON messages(timestamp)
        ''')

        conn.commit()
        conn.close()

    def add_message(self, message: Message) -> bool:
        """
        Add message to persistent storage

        Args:
            message: Message to add

        Returns:
            True if added, False if storage full
        """
        # Check current size
        current_size = self.get_storage_size()
        msg_size = message.get_size()

        if current_size + msg_size > self.max_size:
            # Try to clean old messages
            self._cleanup_old_messages(msg_size)
            current_size = self.get_storage_size()

            if current_size + msg_size > self.max_size:
                return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO messages (timestamp, sender, content, color, type, metadata, size)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            message.timestamp,
            message.sender,
            message.content,
            message.color,
            message.type.value,
            json.dumps(message.metadata),
            msg_size
        ))

        conn.commit()
        conn.close()
        return True

    def get_messages(self, limit: Optional[int] = None, offset: int = 0) -> List[Message]:
        """
        Get messages from storage

        Args:
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List of messages
        """
        from protocol import MessageType

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = 'SELECT timestamp, sender, content, color, type, metadata FROM messages ORDER BY timestamp DESC'

        if limit:
            query += f' LIMIT {limit} OFFSET {offset}'

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        messages = []
        for row in rows:
            timestamp, sender, content, color, msg_type, metadata_json = row
            metadata = json.loads(metadata_json) if metadata_json else {}

            msg = Message(
                MessageType(msg_type),
                sender,
                content,
                color,
                metadata
            )
            msg.timestamp = timestamp
            messages.append(msg)

        return list(reversed(messages))  # Return in chronological order

    def _cleanup_old_messages(self, space_needed: int):
        """Remove oldest messages to free space"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Delete oldest 10% of messages
        cursor.execute('SELECT COUNT(*) FROM messages')
        total = cursor.fetchone()[0]
        to_delete = max(1, total // 10)

        cursor.execute(f'''
            DELETE FROM messages WHERE id IN (
                SELECT id FROM messages ORDER BY timestamp ASC LIMIT {to_delete}
            )
        ''')

        conn.commit()
        conn.close()

    def get_storage_size(self) -> int:
        """Get current storage size in bytes"""
        if not self.db_path.exists():
            return 0
        return self.db_path.stat().st_size

    def get_message_count(self) -> int:
        """Get total message count"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM messages')
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_usage_percentage(self) -> float:
        """Get storage usage percentage"""
        return (self.get_storage_size() / self.max_size) * 100

    def get_size_mb(self) -> float:
        """Get current storage size in MB"""
        return self.get_storage_size() / (1024 * 1024)

    def clear(self):
        """Clear all messages"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM messages')
        conn.commit()
        conn.close()

    def delete_session(self):
        """Delete entire session database"""
        if self.db_path.exists():
            self.db_path.unlink()


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
            Profile dictionary with username, color, emoji, and theme
        """
        if not self.profile_path.exists():
            return self._get_default_profile()

        try:
            with open(self.profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
                # Ensure emoji key exists (migrate old profiles)
                if 'emoji' not in profile:
                    profile['emoji'] = '👤'
                # Remove old avatar key if exists
                if 'avatar' in profile:
                    del profile['avatar']
                # Add theme if missing
                if 'theme' not in profile:
                    profile['theme'] = 'dark'
                # Add bio if missing
                if 'bio' not in profile:
                    profile['bio'] = ''
                return profile
        except (json.JSONDecodeError, IOError):
            return self._get_default_profile()

    def save_profile(self, username: str, color: str, emoji: str = '👤', theme: str = 'dark', bio: str = '') -> bool:
        """
        Save user profile

        Args:
            username: User's display name
            color: Hex color code
            emoji: Profile emoji
            theme: UI theme ('dark' or 'light')
            bio: User biography (max 600 characters)

        Returns:
            True if successful, False otherwise
        """
        # Truncate bio to 600 characters
        bio = bio[:600] if bio else ''

        profile = {
            'username': username,
            'color': color,
            'emoji': emoji,
            'theme': theme,
            'bio': bio
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
            'color': '#00FF00',
            'emoji': '👤',
            'theme': 'dark'
        }

    def get_available_emojis(self) -> List[Dict[str, str]]:
        """Get list of available emojis for profile selection"""
        return [
            {'name': 'Smile', 'emoji': '😀'},
            {'name': 'Cool', 'emoji': '😎'},
            {'name': 'Heart Eyes', 'emoji': '😍'},
            {'name': 'Wink', 'emoji': '😉'},
            {'name': 'Star Eyes', 'emoji': '🤩'},
            {'name': 'Robot', 'emoji': '🤖'},
            {'name': 'Ghost', 'emoji': '👻'},
            {'name': 'Alien', 'emoji': '👽'},
            {'name': 'Cat', 'emoji': '😺'},
            {'name': 'Dog', 'emoji': '🐶'},
            {'name': 'Fox', 'emoji': '🦊'},
            {'name': 'Panda', 'emoji': '🐼'},
            {'name': 'Fire', 'emoji': '🔥'},
            {'name': 'Star', 'emoji': '⭐'},
            {'name': 'Heart', 'emoji': '❤️'},
            {'name': 'Lightning', 'emoji': '⚡'},
            {'name': 'Rocket', 'emoji': '🚀'},
            {'name': 'Trophy', 'emoji': '🏆'},
            {'name': 'Crown', 'emoji': '👑'},
            {'name': 'Diamond', 'emoji': '💎'}
        ]

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
        self.temp_dir = Path.home() / '.bash_messenger' / 'temp_files'
        self._ensure_temp_dir()
        self.file_cache = {}  # file_id -> file_data

    def _ensure_temp_dir(self):
        """Create temp directory if it doesn't exist"""
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, filename: str, data: bytes) -> Optional[str]:
        """
        Save received file to cache

        Args:
            filename: Name of file
            data: File bytes

        Returns:
            file_id (unique identifier) or None if failed
        """
        try:
            import hashlib
            import time

            # Generate unique file ID
            file_id = hashlib.sha256(f"{filename}{time.time()}".encode()).hexdigest()[:16]

            # Store in cache
            self.file_cache[file_id] = {
                'filename': filename,
                'data': data,
                'size': len(data)
            }

            return file_id

        except Exception as e:
            print(f"Failed to save file: {e}")
            return None

    def get_file(self, file_id: str) -> Optional[bytes]:
        """
        Get file data by ID

        Args:
            file_id: Unique file identifier

        Returns:
            File bytes or None if not found
        """
        if file_id in self.file_cache:
            return self.file_cache[file_id]['data']
        return None

    def remove_file(self, file_id: str) -> bool:
        """
        Remove file from cache

        Args:
            file_id: File identifier

        Returns:
            True if removed
        """
        if file_id in self.file_cache:
            del self.file_cache[file_id]
            return True
        return False

    def clear_cache(self):
        """Clear all cached files"""
        self.file_cache.clear()
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
