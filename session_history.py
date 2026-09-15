"""
Session history management
Stores recent sessions for quick reconnection
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class SessionHistory:
    """Manages session history for reconnection"""

    def __init__(self):
        """Initialize session history"""
        self.history_dir = Path.home() / '.bash_messenger'
        self.history_dir.mkdir(exist_ok=True)
        self.history_path = self.history_dir / 'session_history.json'

    def save_session(self, session_key: str, host_ip: str, port: int,
                     connection_key: str, username: str, is_host: bool = False) -> bool:
        """
        Save session to history

        Args:
            session_key: Session key (6 digits)
            host_ip: Host IP address
            port: Connection port
            connection_key: Connection key (8 digits)
            username: User's username
            is_host: Whether this session was hosted by this user

        Returns:
            True if successful
        """
        try:
            history = self.load_history()

            # Create session entry
            session = {
                'session_key': session_key,
                'host_ip': host_ip,
                'port': port,
                'connection_key': connection_key,
                'username': username,
                'is_host': is_host,
                'last_connected': datetime.now().isoformat(),
                'timestamp': datetime.now().timestamp()
            }

            # Add to history (keep last 10 sessions)
            history = [s for s in history if s['session_key'] != session_key]
            history.insert(0, session)
            history = history[:10]

            # Save
            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2)

            return True
        except Exception as e:
            print(f"Failed to save session history: {e}")
            return False

    def load_history(self) -> List[Dict]:
        """
        Load session history

        Returns:
            List of session dictionaries
        """
        if not self.history_path.exists():
            return []

        try:
            with open(self.history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def get_session(self, session_key: str) -> Optional[Dict]:
        """
        Get session by key

        Args:
            session_key: Session key to find

        Returns:
            Session dictionary or None
        """
        history = self.load_history()
        for session in history:
            if session['session_key'] == session_key:
                return session
        return None

    def delete_session(self, session_key: str) -> bool:
        """
        Delete session from history

        Args:
            session_key: Session key to delete

        Returns:
            True if successful
        """
        try:
            history = self.load_history()
            history = [s for s in history if s['session_key'] != session_key]

            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2)

            return True
        except Exception:
            return False

    def clear_history(self) -> bool:
        """
        Clear all session history

        Returns:
            True if successful
        """
        try:
            if self.history_path.exists():
                self.history_path.unlink()
            return True
        except Exception:
            return False
