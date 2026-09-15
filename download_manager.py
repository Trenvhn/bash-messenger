"""
Download manager for file transfers
Handles pending downloads, progress tracking, and file storage
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import os


class PendingDownload:
    """Represents a pending file download"""

    def __init__(self, file_id: str, filename: str, filesize: int, sender: str):
        """
        Initialize pending download

        Args:
            file_id: Unique file identifier
            filename: Original filename
            filesize: File size in bytes
            sender: Username of sender
        """
        self.file_id = file_id
        self.filename = filename
        self.filesize = filesize
        self.sender = sender
        self.timestamp = datetime.now().isoformat()
        self.downloaded_bytes = 0
        self.status = 'pending'  # pending, downloading, completed, failed

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'file_id': self.file_id,
            'filename': self.filename,
            'filesize': self.filesize,
            'sender': self.sender,
            'timestamp': self.timestamp,
            'downloaded_bytes': self.downloaded_bytes,
            'status': self.status
        }

    @staticmethod
    def from_dict(data: Dict) -> 'PendingDownload':
        """Create from dictionary"""
        download = PendingDownload(
            data['file_id'],
            data['filename'],
            data['filesize'],
            data['sender']
        )
        download.timestamp = data['timestamp']
        download.downloaded_bytes = data.get('downloaded_bytes', 0)
        download.status = data.get('status', 'pending')
        return download

    def get_progress_percent(self) -> float:
        """Get download progress percentage"""
        if self.filesize == 0:
            return 100.0
        return (self.downloaded_bytes / self.filesize) * 100

    def get_size_display(self) -> str:
        """Get human-readable size"""
        return self._format_size(self.filesize)

    def get_downloaded_display(self) -> str:
        """Get human-readable downloaded size"""
        return self._format_size(self.downloaded_bytes)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"


class DownloadManager:
    """Manages file downloads and pending files"""

    def __init__(self):
        """Initialize download manager"""
        self.downloads_dir = Path.home() / 'Downloads' / 'bash_messenger'
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

        self.pending_downloads: Dict[str, PendingDownload] = {}
        self.completed_downloads: List[PendingDownload] = []

    def add_pending_download(self, file_id: str, filename: str,
                            filesize: int, sender: str) -> PendingDownload:
        """
        Add a pending download

        Args:
            file_id: Unique file identifier
            filename: Original filename
            filesize: File size in bytes
            sender: Username of sender

        Returns:
            PendingDownload object
        """
        download = PendingDownload(file_id, filename, filesize, sender)
        self.pending_downloads[file_id] = download
        return download

    def get_pending_downloads(self) -> List[PendingDownload]:
        """Get list of pending downloads"""
        return list(self.pending_downloads.values())

    def get_download(self, file_id: str) -> Optional[PendingDownload]:
        """Get download by file ID"""
        return self.pending_downloads.get(file_id)

    def start_download(self, file_id: str) -> bool:
        """
        Mark download as started

        Args:
            file_id: File identifier

        Returns:
            True if successful
        """
        if file_id in self.pending_downloads:
            self.pending_downloads[file_id].status = 'downloading'
            return True
        return False

    def update_progress(self, file_id: str, downloaded_bytes: int):
        """
        Update download progress

        Args:
            file_id: File identifier
            downloaded_bytes: Bytes downloaded so far
        """
        if file_id in self.pending_downloads:
            self.pending_downloads[file_id].downloaded_bytes = downloaded_bytes

    def complete_download(self, file_id: str, file_data: bytes) -> Optional[Path]:
        """
        Complete download and save file

        Args:
            file_id: File identifier
            file_data: File binary data

        Returns:
            Path to saved file or None if failed
        """
        if file_id not in self.pending_downloads:
            return None

        download = self.pending_downloads[file_id]

        try:
            # Generate unique filename if file exists
            filepath = self.downloads_dir / download.filename
            if filepath.exists():
                name = filepath.stem
                ext = filepath.suffix
                counter = 1
                while filepath.exists():
                    filepath = self.downloads_dir / f"{name}_{counter}{ext}"
                    counter += 1

            # Save file
            with open(filepath, 'wb') as f:
                f.write(file_data)

            # Mark as completed
            download.status = 'completed'
            download.downloaded_bytes = len(file_data)
            self.completed_downloads.append(download)
            del self.pending_downloads[file_id]

            return filepath

        except Exception as e:
            download.status = 'failed'
            print(f"Failed to save file: {e}")
            return None

    def remove_pending(self, file_id: str) -> bool:
        """
        Remove pending download

        Args:
            file_id: File identifier

        Returns:
            True if removed
        """
        if file_id in self.pending_downloads:
            del self.pending_downloads[file_id]
            return True
        return False

    def clear_completed(self):
        """Clear completed downloads list"""
        self.completed_downloads.clear()

    def get_downloads_directory(self) -> Path:
        """Get downloads directory path"""
        return self.downloads_dir
