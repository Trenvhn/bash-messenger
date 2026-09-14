"""
Authentication and ban management for Bash Messenger
"""
import time
from typing import Dict, Optional


class BanManager:
    """Manages connection attempt tracking and IP banning"""

    def __init__(self):
        """Initialize ban manager"""
        self.attempts: Dict[str, list] = {}  # IP -> [timestamp, timestamp, ...]
        self.banned: Dict[str, float] = {}   # IP -> unban_timestamp
        self.max_attempts = 3
        self.ban_duration = 120  # 2 minutes in seconds

    def record_attempt(self, ip_address: str) -> int:
        """
        Record connection attempt from IP

        Args:
            ip_address: Client IP address

        Returns:
            Number of attempts in current window
        """
        current_time = time.time()

        # Initialize attempt list for new IP
        if ip_address not in self.attempts:
            self.attempts[ip_address] = []

        # Clean old attempts (older than ban duration)
        self.attempts[ip_address] = [
            t for t in self.attempts[ip_address]
            if current_time - t < self.ban_duration
        ]

        # Record new attempt
        self.attempts[ip_address].append(current_time)

        # Check if should be banned
        if len(self.attempts[ip_address]) >= self.max_attempts:
            self.ban_ip(ip_address)

        return len(self.attempts[ip_address])

    def ban_ip(self, ip_address: str):
        """Ban IP for specified duration"""
        self.banned[ip_address] = time.time() + self.ban_duration

    def is_banned(self, ip_address: str) -> bool:
        """
        Check if IP is currently banned

        Args:
            ip_address: Client IP address

        Returns:
            True if banned, False otherwise
        """
        if ip_address not in self.banned:
            return False

        current_time = time.time()

        # Check if ban has expired
        if current_time >= self.banned[ip_address]:
            # Unban and reset attempts
            del self.banned[ip_address]
            if ip_address in self.attempts:
                self.attempts[ip_address] = []
            return False

        return True

    def get_ban_time_remaining(self, ip_address: str) -> Optional[int]:
        """
        Get remaining ban time in seconds

        Args:
            ip_address: Client IP address

        Returns:
            Remaining seconds or None if not banned
        """
        if not self.is_banned(ip_address):
            return None

        remaining = int(self.banned[ip_address] - time.time())
        return max(0, remaining)

    def get_attempts_remaining(self, ip_address: str) -> int:
        """
        Get remaining connection attempts before ban

        Args:
            ip_address: Client IP address

        Returns:
            Number of attempts remaining
        """
        if self.is_banned(ip_address):
            return 0

        if ip_address not in self.attempts:
            return self.max_attempts

        current_time = time.time()
        recent_attempts = [
            t for t in self.attempts[ip_address]
            if current_time - t < self.ban_duration
        ]

        return max(0, self.max_attempts - len(recent_attempts))

    def clear_ip(self, ip_address: str):
        """Clear all records for an IP (after successful connection)"""
        if ip_address in self.attempts:
            del self.attempts[ip_address]
        if ip_address in self.banned:
            del self.banned[ip_address]

    def get_banned_ips(self) -> list:
        """Get list of currently banned IPs with remaining time"""
        current_time = time.time()
        banned_list = []

        for ip, unban_time in self.banned.items():
            remaining = int(unban_time - current_time)
            if remaining > 0:
                banned_list.append({
                    'ip': ip,
                    'remaining_seconds': remaining
                })

        return banned_list
