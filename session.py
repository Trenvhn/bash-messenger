"""
Session management for Bash Messenger
Handles session key generation and session state
"""
import time
import hashlib
import random
import string
from typing import Optional


def generate_session_key(host_ip: str) -> str:
    """
    Generate 6-digit session key from host IP and timestamp

    Algorithm:
    - Extract last octet of IP
    - Combine with current timestamp
    - Hash and convert to 6-character alphanumeric

    Args:
        host_ip: Host IP address (e.g., "192.168.80.5")

    Returns:
        6-character alphanumeric session key (e.g., "5GHDYJ")
    """
    # Extract last octet
    last_octet = host_ip.split('.')[-1]

    # Get current timestamp
    timestamp = str(int(time.time()))

    # Combine and hash
    data = f"{last_octet}{timestamp}".encode('utf-8')
    hash_digest = hashlib.sha256(data).hexdigest()

    # Convert to alphanumeric (base36-like)
    # Take first 6 characters and convert to uppercase alphanumeric
    session_key = ""
    chars = string.ascii_uppercase + string.digits

    for i in range(6):
        # Use hash bytes to select characters
        index = int(hash_digest[i*2:i*2+2], 16) % len(chars)
        session_key += chars[index]

    return session_key


def generate_connection_key() -> str:
    """
    Generate 8-digit random connection key (OTP)

    Returns:
        8-digit numeric string
    """
    return ''.join(random.choices(string.digits, k=8))


class SessionManager:
    """Manages session state and metadata"""

    def __init__(self, session_key: str, connection_key: str, is_host: bool):
        """
        Initialize session manager

        Args:
            session_key: 6-digit session identifier
            connection_key: 8-digit connection password
            is_host: True if this is the host, False if client
        """
        self.session_key = session_key
        self.connection_key = connection_key
        self.is_host = is_host
        self.created_at = time.time()
        self.connected_users = []
        self.total_data_size = 0  # bytes
        self.max_data_size = 265 * 1024 * 1024  # 265 MB
        self.message_count = 0

    def add_user(self, username: str, address: Optional[tuple] = None):
        """Add user to session"""
        self.connected_users.append({
            'username': username,
            'address': address,
            'connected_at': time.time()
        })

    def remove_user(self, username: str):
        """Remove user from session"""
        self.connected_users = [u for u in self.connected_users if u['username'] != username]

    def can_accept_data(self, size_bytes: int) -> bool:
        """Check if session can accept more data"""
        return (self.total_data_size + size_bytes) <= self.max_data_size

    def add_data(self, size_bytes: int) -> bool:
        """
        Add data to session total

        Returns:
            True if successful, False if limit exceeded
        """
        if self.can_accept_data(size_bytes):
            self.total_data_size += size_bytes
            return True
        return False

    def get_usage_percentage(self) -> float:
        """Get session data usage as percentage"""
        return (self.total_data_size / self.max_data_size) * 100

    def get_session_info(self) -> dict:
        """Get session metadata"""
        return {
            'session_key': self.session_key,
            'is_host': self.is_host,
            'created_at': self.created_at,
            'connected_users': len(self.connected_users),
            'max_users': 51,  # 1 host + 50 clients
            'data_usage_mb': self.total_data_size / (1024 * 1024),
            'max_data_mb': 265,
            'usage_percentage': self.get_usage_percentage(),
            'message_count': self.message_count
        }
