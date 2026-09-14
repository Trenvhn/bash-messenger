# Bash Messenger - Architecture Plan

## Overview
Self-hosted terminal messenger with encrypted P2P communication supporting 1 host + 4 clients.

## System Architecture

### 1. Network Layer (Direct P2P)
```
Host (Server Socket)
├── Binds to 0.0.0.0:5555 (configurable)
├── Accepts up to 4 client connections
├── Validates connection keys (hash-based)
└── Broadcasts messages to all connected clients

Client (Socket)
├── Connects to host IP:port
├── Sends hashed connection key
├── Receives and decrypts messages
└── Sends encrypted messages
```

### 2. Session Management
**Session Key Generation:**
- Input: Host IP (e.g., 192.168.80.5) + Unix timestamp
- Algorithm: Extract last octet + timestamp hash → 6-digit alphanumeric
- Example: `5GHDYJ`

**Connection Key Generation:**
- 8-digit random numeric OTP
- Stored as SHA-256 hash on host
- Client sends hash for validation
- Combined with session key for encryption seed

### 3. Security Components

**Authentication Flow:**
1. Client requests to join session with session key
2. Client prompts for 8-digit connection key
3. Client hashes connection key (SHA-256)
4. Client sends hash to host
5. Host compares hashes
6. On match: Connection accepted
7. On mismatch: Attempt counter increments
8. After 3 failed attempts: IP banned for 2 minutes

**Encryption (AES-256-GCM):**
- Master key derived from: session_key + connection_key (PBKDF2)
- Each message encrypted with unique nonce
- Message format: `nonce + ciphertext + tag`

### 4. Message Protocol

**Message Types:**
```python
{
    "type": "text|file|typing|system",
    "sender": "username",
    "content": "encrypted_payload",
    "timestamp": 1694785200,
    "color": "#FF5733",
    "metadata": {...}
}
```

**File Transfer:**
- Chunk files into 1MB pieces
- Encrypt each chunk
- Track progress with metadata
- Enforce 265MB total session limit

### 5. Storage Management

**RAM Storage:**
- In-memory message buffer (max 265MB)
- FIFO eviction when limit reached
- Per-session statistics tracking

**Persistent Storage:**
```
~/.bash_messenger/
├── profile.json (username, color preference)
└── banned_ips.json (temporary ban list)
```

### 6. User Interface (Terminal TUI)

**Layout:**
```
┌─────────────────────────────────────────┐
│ Session: 5GHDYJ | Connected: 3/4        │
├─────────────────────────────────────────┤
│                                         │
│ [Alice] Hey everyone!                   │
│ [Bob] Hi Alice                          │
│ [You] Hello!                            │
│ [System] Charlie is typing...           │
│                                         │
├─────────────────────────────────────────┤
│ > Type message...                       │
└─────────────────────────────────────────┘
```

**Menus:**
1. **Startup Menu:**
   - Create Session (become host)
   - Join Session (become client)
   - Profile Settings
   - Exit

2. **Profile Settings:**
   - Change username
   - Change color (16 preset colors)

3. **In-Session Commands:**
   - `/quit` - Leave session
   - `/users` - List connected users
   - `/file <path>` - Send file
   - `/clear` - Clear screen

## Module Structure

```
bash_messenger/
├── main.py                 # Entry point, UI, menu system
├── session.py             # Session key generation, session manager
├── network.py             # Socket handling, host/client logic
├── encryption.py          # AES-256 encryption, key derivation
├── auth.py                # Connection key validation, ban manager
├── storage.py             # RAM buffer, profile management
├── protocol.py            # Message serialization, protocol
├── ui.py                  # Terminal UI components (curses/rich)
└── utils.py               # Helpers, logging

requirements.txt           # Python dependencies
install.sh                # Unix installer
install.bat               # Windows installer
README.md                 # User documentation
```

## Dependencies
- `cryptography` - AES-256 encryption, hashing
- `rich` - Terminal UI with colors and formatting
- `asyncio` - Async networking
- `python-dotenv` - Configuration (optional)

## Performance Targets
- Message latency: < 100ms (local network)
- Memory usage: < 300MB (265MB + overhead)
- Support 5 concurrent users
- Handle 1000 messages/minute

## Security Considerations
1. ✅ Hash-based authentication (SHA-256)
2. ✅ AES-256-GCM encryption
3. ✅ Rate limiting (3 attempts, 2-min ban)
4. ✅ No plaintext password storage
5. ✅ Unique nonces per message
6. ⚠️ Host must configure port forwarding
7. ⚠️ Host IP exposed in session key (encrypted)
8. ⚠️ No replay attack protection (out of scope)

## Future Enhancements (v2)
- NAT traversal / relay server
- Multi-session support per host
- Persistent message history (encrypted)
- End-to-end encryption per user pair
- Voice/video support
