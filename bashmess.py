#!/usr/bin/env python3
"""
Bash Messenger Launcher
Quick launcher for bash_messenger.py
"""
import sys
from pathlib import Path

# Add the installation directory to path
install_dir = Path(__file__).parent
sys.path.insert(0, str(install_dir))

# Import and run main application
from bash_messenger import main

if __name__ == "__main__":
    main()
