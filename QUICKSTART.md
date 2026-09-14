# Bash Messenger - Quick Start Guide

## Installation

### Windows
1. Download or clone the repository
2. Open Command Prompt or PowerShell
3. Navigate to the bash_messenger folder
4. Run: `install.bat`

### Linux/macOS
1. Download or clone the repository
2. Open Terminal
3. Navigate to the bash_messenger folder
4. Run: `chmod +x install.sh && ./install.sh`

## Running the Program

After installation, simply type:
```
bashmess
```

## Creating Your First Session

### As Host (Person Starting the Chat)

1. Run `bashmess`
2. Choose option **1** (Create Session)
3. Write down the **Session Key** and **Connection Key**
4. Share these keys with your friends
5. Wait for them to connect
6. Start chatting!

**Important**: If connecting over internet, you need to:
- Forward the port (default: 5555) on your router
- Share your public IP with friends

### As Client (Person Joining the Chat)

1. Get the Session Key and Connection Key from the host
2. Run `bashmess`
3. Choose option **2** (Join Session)
4. Enter the Session Key (6 digits)
5. Enter the Host's IP address
6. Enter the port (default: 5555)
7. Enter the Connection Key (8 digits)
8. Start chatting!

## Commands While Chatting

- `/quit` - Leave the session
- `/users` - See who's connected
- `/file <filepath>` - Send a file
- `/clear` - Clear your screen

## Customizing Your Profile

1. Run `bashmess`
2. Choose option **3** (Profile Settings)
3. Change your username
4. Pick your favorite color

## Tips

- The host must keep the program running for the session to stay active
- When the host closes the program, everyone gets disconnected
- All messages are encrypted and only stored in RAM
- Maximum 5 people per session (1 host + 4 clients)
- You can share files up to 265MB total per session

## Troubleshooting

**Can't connect?**
- Check the IP address is correct
- Make sure the port is open (firewall/router)
- Verify the Connection Key is correct

**Banned after 3 attempts?**
- Wait 2 minutes and try again
- Make sure you're entering the correct Connection Key

**Need help?**
- Check the full README.md for detailed documentation
- Open an issue on GitHub

---

Happy chatting! 🎉
