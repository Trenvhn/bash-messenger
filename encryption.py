"""
Encryption module for Bash Messenger
Handles AES-256-GCM encryption/decryption and key derivation
"""
import os
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class MessageEncryption:
    """Handles message encryption and key derivation"""

    def __init__(self, session_key: str, connection_key: str):
        """
        Initialize encryption with session and connection keys

        Args:
            session_key: 6-digit session identifier
            connection_key: 8-digit connection password
        """
        self.master_key = self._derive_key(session_key, connection_key)
        self.cipher = AESGCM(self.master_key)

    def _derive_key(self, session_key: str, connection_key: str) -> bytes:
        """
        Derive 256-bit encryption key from session and connection keys

        Args:
            session_key: Session identifier
            connection_key: Connection password

        Returns:
            32-byte AES-256 key
        """
        # Combine keys as password
        password = f"{session_key}{connection_key}".encode('utf-8')

        # Use session key as salt (deterministic for same session)
        salt = hashlib.sha256(session_key.encode('utf-8')).digest()

        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )

        return kdf.derive(password)

    def encrypt(self, plaintext: str) -> bytes:
        """
        Encrypt message with AES-256-GCM

        Args:
            plaintext: Message to encrypt

        Returns:
            nonce (12 bytes) + ciphertext + tag (16 bytes)
        """
        # Generate random nonce (96 bits)
        nonce = os.urandom(12)

        # Encrypt with associated data for integrity
        ciphertext = self.cipher.encrypt(nonce, plaintext.encode('utf-8'), None)

        # Return nonce + ciphertext (ciphertext includes auth tag)
        return nonce + ciphertext

    def decrypt(self, encrypted_data: bytes) -> str:
        """
        Decrypt message

        Args:
            encrypted_data: nonce + ciphertext + tag

        Returns:
            Decrypted plaintext string

        Raises:
            ValueError: If decryption fails (wrong key or tampered data)
        """
        # Extract nonce and ciphertext
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]

        # Decrypt and verify
        plaintext_bytes = self.cipher.decrypt(nonce, ciphertext, None)

        return plaintext_bytes.decode('utf-8')


def hash_connection_key(connection_key: str) -> str:
    """
    Hash connection key for secure storage and validation

    Args:
        connection_key: 8-digit connection password

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(connection_key.encode('utf-8')).hexdigest()


def verify_connection_key(input_key: str, stored_hash: str) -> bool:
    """
    Verify connection key against stored hash

    Args:
        input_key: User-provided connection key
        stored_hash: Stored hash to compare against

    Returns:
        True if key matches, False otherwise
    """
    input_hash = hash_connection_key(input_key)
    return input_hash == stored_hash
