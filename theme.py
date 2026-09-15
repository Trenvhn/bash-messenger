"""
Theme module for Bash Messenger
Handles dark mode and light mode color schemes
"""
from typing import Dict


class Theme:
    """Theme manager for dark and light modes"""

    DARK_MODE = {
        'name': 'Dark Mode',
        'background': '#000000',
        'primary': 'bright_cyan',
        'secondary': 'cyan',
        'text': 'white',
        'text_dim': 'bright_black',
        'success': 'bright_green',
        'warning': 'bright_yellow',
        'error': 'bright_red',
        'border': 'bright_blue',
        'accent': 'bright_magenta',
        'system': 'yellow',
        'timestamp': 'bright_black',
        'input_prompt': 'bright_cyan',
        'banner': 'bright_cyan',
        'menu_header': 'bright_white',
        'menu_item': 'bright_green',
        'menu_desc': 'bright_black'
    }

    LIGHT_MODE = {
        'name': 'Light Mode',
        'background': '#FFFFFF',
        'primary': 'blue',
        'secondary': 'cyan',
        'text': 'black',
        'text_dim': 'bright_black',
        'success': 'green',
        'warning': 'yellow',
        'error': 'red',
        'border': 'blue',
        'accent': 'magenta',
        'system': 'bright_yellow',
        'timestamp': 'bright_black',
        'input_prompt': 'blue',
        'banner': 'blue',
        'menu_header': 'black',
        'menu_item': 'green',
        'menu_desc': 'bright_black'
    }

    def __init__(self, mode: str = 'dark'):
        """
        Initialize theme

        Args:
            mode: 'dark' or 'light'
        """
        self.mode = mode
        self.colors = self.DARK_MODE if mode == 'dark' else self.LIGHT_MODE

    def get(self, key: str) -> str:
        """Get color for a key"""
        return self.colors.get(key, 'white')

    def switch_mode(self):
        """Toggle between dark and light mode"""
        self.mode = 'light' if self.mode == 'dark' else 'dark'
        self.colors = self.DARK_MODE if self.mode == 'dark' else self.LIGHT_MODE

    def get_mode(self) -> str:
        """Get current mode"""
        return self.mode

    def get_mode_name(self) -> str:
        """Get current mode display name"""
        return self.colors['name']
