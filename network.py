"""
Network module for Bash Messenger
Handles host and client socket operations
"""
import socket
import asyncio
import json
from typing import Optional, Callable, Dict, List
from encryption import MessageEncryption, hash_connection_key
from protocol import Message, MessageType
from auth import BanManager


class Host:
    """Host server that accepts client connections"""

    def __init__(self, session_key: str, connection_key_hash: str,
                 on_message: Callable, on_user_join: Callable, on_user_leave: Callable):
        """
        Initialize host server

        Args:
            session_key: 6-digit session key
            connection_key_hash: Hashed connection password
            on_message: Callback for received messages
            on_user_join: Callback when user joins
            on_user_leave: Callback when user leaves
        """
        self.session_key = session_key
        self.connection_key_hash = connection_key_hash
        self.on_message = on_message
        self.on_user_join = on_user_join
        self.on_user_leave = on_user_leave

        self.clients: Dict[str, asyncio.StreamWriter] = {}  # username -> writer
        self.client_info: Dict[str, dict] = {}  # username -> {address, color}
        self.max_clients = 4
        self.ban_manager = BanManager()
        self.running = False
        self.server = None
        self.encryption: Optional[MessageEncryption] = None

    def set_encryption(self, encryption: MessageEncryption):
        """Set encryption handler"""
        self.encryption = encryption

    async def start(self, host: str = '0.0.0.0', port: int = 5555):
        """
        Start host server

        Args:
            host: Bind address
            port: Listen port
        """
        self.running = True
        self.server = await asyncio.start_server(
            self._handle_client, host, port
        )

        addr = self.server.sockets[0].getsockname()
        print(f"[Host] Server started on {addr[0]}:{addr[1]}")

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle new client connection"""
        addr = writer.get_extra_info('peername')
        ip_address = addr[0]

        print(f"[Host] Connection attempt from {ip_address}")

        # Check if IP is banned
        if self.ban_manager.is_banned(ip_address):
            remaining = self.ban_manager.get_ban_time_remaining(ip_address)
            error_msg = json.dumps({
                'status': 'banned',
                'remaining_seconds': remaining
            })
            writer.write(error_msg.encode('utf-8'))
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        # Check max clients
        if len(self.clients) >= self.max_clients:
            error_msg = json.dumps({'status': 'full'})
            writer.write(error_msg.encode('utf-8'))
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        try:
            # Receive authentication data
            data = await reader.read(4096)
            auth_data = json.loads(data.decode('utf-8'))

            username = auth_data.get('username')
            connection_key_hash_client = auth_data.get('connection_key_hash')
            color = auth_data.get('color', '#FFFFFF')

            # Verify connection key
            if connection_key_hash_client != self.connection_key_hash:
                attempts = self.ban_manager.record_attempt(ip_address)
                remaining = self.ban_manager.get_attempts_remaining(ip_address)

                error_msg = json.dumps({
                    'status': 'auth_failed',
                    'attempts_remaining': remaining
                })
                writer.write(error_msg.encode('utf-8'))
                await writer.drain()
                writer.close()
                await writer.wait_closed()
                return

            # Authentication successful
            self.ban_manager.clear_ip(ip_address)

            # Send success
            success_msg = json.dumps({'status': 'connected'})
            writer.write(success_msg.encode('utf-8'))
            await writer.drain()

            # Add client
            self.clients[username] = writer
            self.client_info[username] = {'address': addr, 'color': color}

            # Notify user joined
            await self.on_user_join(username, color)

            # Handle client messages
            await self._handle_client_messages(reader, writer, username)

        except Exception as e:
            print(f"[Host] Client error: {e}")
        finally:
            if username in self.clients:
                del self.clients[username]
                del self.client_info[username]
                await self.on_user_leave(username)
            writer.close()
            await writer.wait_closed()

    async def _handle_client_messages(self, reader: asyncio.StreamReader,
                                     writer: asyncio.StreamWriter, username: str):
        """Handle messages from connected client"""
        while self.running:
            try:
                # Read message length first (4 bytes)
                length_data = await reader.readexactly(4)
                msg_length = int.from_bytes(length_data, 'big')

                # Read encrypted message
                encrypted_data = await reader.readexactly(msg_length)

                # Decrypt
                decrypted_json = self.encryption.decrypt(encrypted_data)
                message = Message.from_json(decrypted_json)

                # Broadcast to all clients and handle locally
                await self.broadcast_message(message)
                await self.on_message(message)

            except asyncio.IncompleteReadError:
                break
            except Exception as e:
                print(f"[Host] Error handling message from {username}: {e}")
                break

    async def broadcast_message(self, message: Message, exclude: Optional[str] = None):
        """
        Broadcast message to all connected clients

        Args:
            message: Message to broadcast
            exclude: Username to exclude from broadcast
        """
        if not self.encryption:
            return

        # Encrypt message
        encrypted_data = self.encryption.encrypt(message.to_json())
        msg_length = len(encrypted_data).to_bytes(4, 'big')

        # Send to all clients
        for username, writer in list(self.clients.items()):
            if username != exclude:
                try:
                    writer.write(msg_length + encrypted_data)
                    await writer.drain()
                except Exception as e:
                    print(f"[Host] Error sending to {username}: {e}")

    async def send_message(self, message: Message):
        """Send message from host to all clients"""
        await self.broadcast_message(message)
        await self.on_message(message)

    async def stop(self):
        """Stop host server"""
        self.running = False

        # Close all client connections
        for writer in self.clients.values():
            writer.close()
            await writer.wait_closed()

        # Close server
        if self.server:
            self.server.close()
            await self.server.wait_closed()


class Client:
    """Client that connects to host"""

    def __init__(self, session_key: str, connection_key: str, username: str, color: str,
                 on_message: Callable, on_connected: Callable, on_disconnected: Callable):
        """
        Initialize client

        Args:
            session_key: 6-digit session key
            connection_key: 8-digit connection password (plaintext)
            username: User's display name
            color: User's color
            on_message: Callback for received messages
            on_connected: Callback when connected
            on_disconnected: Callback when disconnected
        """
        self.session_key = session_key
        self.connection_key = connection_key
        self.username = username
        self.color = color
        self.on_message = on_message
        self.on_connected = on_connected
        self.on_disconnected = on_disconnected

        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.encryption: Optional[MessageEncryption] = None
        self.running = False

    async def connect(self, host_ip: str, port: int = 5555) -> bool:
        """
        Connect to host

        Args:
            host_ip: Host IP address
            port: Host port

        Returns:
            True if connected, False otherwise
        """
        try:
            self.reader, self.writer = await asyncio.open_connection(host_ip, port)

            # Send authentication
            auth_data = {
                'username': self.username,
                'connection_key_hash': hash_connection_key(self.connection_key),
                'color': self.color
            }
            self.writer.write(json.dumps(auth_data).encode('utf-8'))
            await self.writer.drain()

            # Receive response
            response_data = await self.reader.read(4096)
            response = json.loads(response_data.decode('utf-8'))

            if response['status'] == 'connected':
                # Initialize encryption
                self.encryption = MessageEncryption(self.session_key, self.connection_key)
                self.running = True

                # Start receiving messages
                asyncio.create_task(self._receive_messages())

                await self.on_connected()
                return True
            else:
                # Connection failed
                error = response.get('status', 'unknown_error')
                print(f"[Client] Connection failed: {error}")
                if 'attempts_remaining' in response:
                    print(f"[Client] Attempts remaining: {response['attempts_remaining']}")
                if 'remaining_seconds' in response:
                    print(f"[Client] Banned for {response['remaining_seconds']} seconds")
                return False

        except Exception as e:
            print(f"[Client] Connection error: {e}")
            return False

    async def _receive_messages(self):
        """Receive messages from host"""
        while self.running:
            try:
                # Read message length
                length_data = await self.reader.readexactly(4)
                msg_length = int.from_bytes(length_data, 'big')

                # Read encrypted message
                encrypted_data = await self.reader.readexactly(msg_length)

                # Decrypt
                decrypted_json = self.encryption.decrypt(encrypted_data)
                message = Message.from_json(decrypted_json)

                # Handle message
                await self.on_message(message)

            except asyncio.IncompleteReadError:
                break
            except Exception as e:
                print(f"[Client] Error receiving message: {e}")
                break

        await self.on_disconnected()

    async def send_message(self, message: Message):
        """Send message to host"""
        if not self.encryption or not self.writer:
            return

        # Encrypt message
        encrypted_data = self.encryption.encrypt(message.to_json())
        msg_length = len(encrypted_data).to_bytes(4, 'big')

        # Send
        self.writer.write(msg_length + encrypted_data)
        await self.writer.drain()

    async def disconnect(self):
        """Disconnect from host"""
        self.running = False
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
