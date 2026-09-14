"""
Message protocol for Bash Messenger
Handles message serialization and protocol definitions
"""
import json
import time
from typing import Dict, Any, Optional
from enum import Enum


class MessageType(Enum):
    """Message type enumeration"""
    TEXT = "text"
    FILE = "file"
    FILE_CHUNK = "file_chunk"
    TYPING = "typing"
    SYSTEM = "system"
    USER_JOIN = "user_join"
    USER_LEAVE = "user_leave"
    HEARTBEAT = "heartbeat"


class Message:
    """Message protocol class"""

    def __init__(self, msg_type: MessageType, sender: str, content: str,
                 color: str = "#FFFFFF", metadata: Optional[Dict] = None):
        """
        Create a message

        Args:
            msg_type: Type of message
            sender: Username of sender
            content: Message content
            color: Hex color for username display
            metadata: Additional message metadata
        """
        self.type = msg_type
        self.sender = sender
        self.content = content
        self.color = color
        self.timestamp = time.time()
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            'type': self.type.value,
            'sender': self.sender,
            'content': self.content,
            'color': self.color,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }

    def to_json(self) -> str:
        """Serialize message to JSON"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Deserialize message from JSON"""
        data = json.loads(json_str)
        msg = cls(
            msg_type=MessageType(data['type']),
            sender=data['sender'],
            content=data['content'],
            color=data.get('color', '#FFFFFF'),
            metadata=data.get('metadata', {})
        )
        msg.timestamp = data['timestamp']
        return msg

    def get_size(self) -> int:
        """Get message size in bytes"""
        return len(self.to_json().encode('utf-8'))


class FileMessage:
    """File transfer message handler"""

    CHUNK_SIZE = 1024 * 1024  # 1 MB chunks

    def __init__(self, filename: str, file_data: bytes, sender: str, color: str):
        """
        Create file transfer message

        Args:
            filename: Name of file
            file_data: File bytes
            sender: Username of sender
            color: User color
        """
        self.filename = filename
        self.file_data = file_data
        self.sender = sender
        self.color = color
        self.total_size = len(file_data)
        self.total_chunks = (self.total_size + self.CHUNK_SIZE - 1) // self.CHUNK_SIZE

    def get_chunks(self):
        """
        Generate file chunks for transfer

        Yields:
            Message objects for each chunk
        """
        for i in range(self.total_chunks):
            start = i * self.CHUNK_SIZE
            end = min(start + self.CHUNK_SIZE, self.total_size)
            chunk_data = self.file_data[start:end]

            # Encode chunk as base64 for JSON compatibility
            import base64
            chunk_b64 = base64.b64encode(chunk_data).decode('utf-8')

            metadata = {
                'filename': self.filename,
                'chunk_index': i,
                'total_chunks': self.total_chunks,
                'chunk_size': len(chunk_data),
                'total_size': self.total_size
            }

            yield Message(
                msg_type=MessageType.FILE_CHUNK,
                sender=self.sender,
                content=chunk_b64,
                color=self.color,
                metadata=metadata
            )


class FileAssembler:
    """Assembles file chunks back into complete file"""

    def __init__(self):
        """Initialize file assembler"""
        self.active_transfers: Dict[str, Dict] = {}  # filename -> {chunks, metadata}

    def add_chunk(self, message: Message) -> Optional[bytes]:
        """
        Add file chunk and check if complete

        Args:
            message: File chunk message

        Returns:
            Complete file bytes if all chunks received, None otherwise
        """
        import base64

        metadata = message.metadata
        filename = metadata['filename']
        chunk_index = metadata['chunk_index']
        total_chunks = metadata['total_chunks']

        # Initialize transfer if new
        if filename not in self.active_transfers:
            self.active_transfers[filename] = {
                'chunks': {},
                'metadata': metadata
            }

        # Decode and store chunk
        chunk_data = base64.b64decode(message.content.encode('utf-8'))
        self.active_transfers[filename]['chunks'][chunk_index] = chunk_data

        # Check if complete
        if len(self.active_transfers[filename]['chunks']) == total_chunks:
            # Assemble file
            file_data = b''
            for i in range(total_chunks):
                file_data += self.active_transfers[filename]['chunks'][i]

            # Clean up
            del self.active_transfers[filename]

            return file_data

        return None

    def get_progress(self, filename: str) -> Optional[float]:
        """
        Get transfer progress for a file

        Args:
            filename: Name of file

        Returns:
            Progress as percentage (0-100) or None if not found
        """
        if filename not in self.active_transfers:
            return None

        chunks_received = len(self.active_transfers[filename]['chunks'])
        total_chunks = self.active_transfers[filename]['metadata']['total_chunks']

        return (chunks_received / total_chunks) * 100
