# Bash Messenger

**Encrypted P2P Terminal Messenger with Session-Based Architecture**

A secure, lightweight terminal-based chat application that enables encrypted peer-to-peer communication without requiring third-party servers. Perfect for private conversations, team collaboration, and secure file sharing.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Features

✨ **Secure & Private**
- AES-256-GCM encryption for all messages
- Hash-based authentication (SHA-256)
- Direct P2P connection (no third-party servers)
- Two session types:
  - **Temporary**: RAM-only storage (265MB), ends when closed
  - **Persistent**: Disk-based storage (2GB), saves message history

🚀 **Easy to Use**
- Simple terminal interface with colors
- Quick setup with session keys
- No account registration needed
- Cross-platform support (Windows, Linux, macOS)

💬 **Rich Communication**
- Text messaging with emoji support
- File sharing (up to 265MB per session)
- Typing indicators
- Real-time user presence
- Color-coded usernames

🔒 **Security Features**
- One-time 8-digit connection passwords
- Rate limiting (3 attempts, 2-minute ban)
- Session-based encryption keys
- No plaintext credential storage

## Architecture

- **Session-based**: 1 host + 4 clients (5 users max per session)
- **Session Key**: 6-digit encrypted identifier derived from host IP + timestamp
- **Connection Key**: 8-digit random OTP stored as hash
- **Encryption**: AES-256-GCM with PBKDF2 key derivation
- **Transport**: Direct TCP socket connections over internet
- **Storage**: RAM-only message buffer (265MB limit)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Internet connection

### Quick Install

**Windows:**
```cmd
git clone https://github.com/samseatt/bash-messenger.git
cd bash-messenger
install.bat
```

**Linux/macOS:**
```bash
git clone https://github.com/samseatt/bash-messenger.git
cd bash-messenger
chmod +x install.sh
./install.sh
```

### Manual Installation

```bash
pip install -r requirements.txt
```

## Usage

### Starting Bash Messenger

Simply run:
```bash
bashmess
```

Or directly:
```bash
python3 bash_messenger.py
```

### Creating a Session (Host)

1. Launch Bash Messenger
2. Select **"1. Create Session (Host)"**
3. Note your Session Key (6 digits) and Connection Key (8 digits)
4. Choose a port (default: 5555)
5. **Important**: Configure port forwarding on your router if clients are connecting over internet
6. Share the Session Key and Connection Key with clients

**Example:**
```
Session Key: 5GHDYJ
Connection Key: 87654321
Port: 5555
```

### Joining a Session (Client)

1. Launch Bash Messenger
2. Select **"2. Join Session (Client)"**
3. Enter the Session Key provided by host
4. Enter the Host's public IP address
5. Enter the port (default: 5555)
6. Enter the Connection Key
7. Start chatting!

### Profile Settings

Customize your username and display color:
1. Select **"3. Profile Settings"** from main menu
2. Choose from 16 preset colors
3. Settings are saved locally

### In-Chat Commands

**All Users:**
- `/quit` - Leave the session
- `/users` - List connected users
- `/file <path>` - Send a file
- `/clear` - Clear screen
- `/history [count]` - View message history (persistent sessions only)

**Host Only:**
- `/kick <username>` - Remove a user from the session
- `/ban <username>` - Ban a user's IP address permanently

## Security Considerations

### What Bash Messenger Protects Against

✅ Message eavesdropping (AES-256 encryption)  
✅ Unauthorized access (hash-based authentication)  
✅ Brute-force attacks (rate limiting with IP bans)  
✅ Man-in-the-middle (authenticated encryption with GCM)  
✅ Password exposure (SHA-256 hashed storage)

### What Bash Messenger Does NOT Protect Against

⚠️ **Replay attacks** - Out of scope for v1.0  
⚠️ **Host compromise** - If host machine is compromised, session is compromised  
⚠️ **Network metadata** - Connection patterns visible to ISP/network admin  
⚠️ **Endpoint security** - Messages visible in RAM and terminal scrollback

### Network Setup

**For Internet Connections:**
- Host must configure **port forwarding** on their router
- Host must share their **public IP address** with clients
- Firewall must allow incoming connections on chosen port

**For Local Network (LAN):**
- Use host's local IP address (e.g., 192.168.1.100)
- No port forwarding needed

## Configuration

### Default Settings

- **Port**: 5555
- **Max Clients**: 4 (+ 1 host = 5 total)
- **Session Data Limit**: 265 MB
- **File Chunk Size**: 1 MB
- **Max Connection Attempts**: 3
- **Ban Duration**: 2 minutes
- **Profile Location**: `~/.bash_messenger/profile.json`
- **Downloads Location**: `~/.bash_messenger/downloads/`

### Customization

Edit configuration in `bash_messenger.py`:
```python
MAX_CLIENTS = 4
MAX_SESSION_SIZE = 265 * 1024 * 1024  # bytes
DEFAULT_PORT = 5555
BAN_DURATION = 120  # seconds
MAX_ATTEMPTS = 3
```

## File Structure

```
bash-messenger/
├── bash_messenger.py      # Main application
├── session.py             # Session management
├── network.py             # Host/client networking
├── encryption.py          # AES-256 encryption
├── auth.py                # Authentication & banning
├── protocol.py            # Message protocol
├── storage.py             # RAM buffer & profile
├── bashmess               # Unix launcher
├── bashmess.bat           # Windows launcher
├── bashmess.py            # Python launcher
├── install.sh             # Unix installer
├── install.bat            # Windows installer
├── requirements.txt       # Python dependencies
├── README.md              # This file
└── ARCHITECTURE.md        # Technical architecture
```

## Troubleshooting

### "Connection refused" error

- **Check firewall**: Allow incoming connections on the port
- **Check port forwarding**: Configure router NAT/port forwarding
- **Verify host IP**: Use public IP for internet, local IP for LAN
- **Check port**: Ensure host and client use same port number

### "Authentication failed" error

- **Verify connection key**: Must match exactly (case-sensitive)
- **Check attempts**: Wait 2 minutes if IP is banned
- **Session key**: Ensure correct 6-digit session key

### "Session full" error

- Maximum 5 users per session (1 host + 4 clients)
- Host can increase MAX_CLIENTS in configuration

### File transfer fails

- Check session data limit (265 MB total)
- Verify file path is correct
- Ensure stable network connection

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Structure

- **Async I/O**: Uses `asyncio` for non-blocking network operations
- **Modular Design**: Separated concerns (network, encryption, storage)
- **Type Hints**: Python type annotations for better code quality
- **Rich UI**: Terminal UI powered by `rich` library

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Technical Specifications

### Encryption

- **Algorithm**: AES-256-GCM (Galois/Counter Mode)
- **Key Derivation**: PBKDF2-HMAC-SHA256 (100,000 iterations)
- **Nonce**: 96-bit random (unique per message)
- **Authentication**: Built-in GMAC tag (128-bit)

### Network Protocol

```
Message Format:
[4 bytes: length] [encrypted payload]

Encrypted Payload:
[12 bytes: nonce] [ciphertext] [16 bytes: auth tag]

Message JSON:
{
  "type": "text|file|typing|system",
  "sender": "username",
  "content": "message",
  "timestamp": 1694785200,
  "color": "#FF5733",
  "metadata": {}
}
```

### Performance

- **Latency**: < 100ms (local network)
- **Memory**: < 300MB (265MB data + overhead)
- **Throughput**: 1000+ messages/minute
- **Concurrent Users**: Up to 5

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Python](https://www.python.org/)
- UI powered by [Rich](https://github.com/Textualize/rich)
- Encryption by [cryptography](https://cryptography.io/)

## Roadmap

### Version 1.0 ✅
- [x] Direct P2P messaging
- [x] AES-256 encryption
- [x] File sharing
- [x] Session management
- [x] Rate limiting
- [x] Profile settings

### Version 2.0 (Planned)
- [ ] NAT traversal / STUN support
- [ ] Relay server fallback
- [ ] End-to-end per-user encryption
- [ ] Message persistence (encrypted)
- [ ] Multi-session support
- [ ] Plugin system

## Support

- **Issues**: [GitHub Issues](https://github.com/samseatt/bash-messenger/issues)
- **Discussions**: [GitHub Discussions](https://github.com/samseatt/bash-messenger/discussions)
- **Email**: support@bashmenenger.dev

## Security Disclosure

If you discover a security vulnerability, please email security@bashmessenger.dev instead of using the issue tracker.

---

**Made with ❤️ for secure communication**

*Remember: The session ends when the host closes the program. Share responsibly!*
