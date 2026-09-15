"""
Profile picture module for Bash Messenger
Handles 16x16 ASCII art profile pictures
"""
from typing import List, Optional


class ProfilePicture:
    """Handles 16x16 ASCII art profile pictures"""

    # Predefined 16x16 ASCII art avatars
    AVATARS = {
        "default": [
            "    ________    ",
            "   /        \\   ",
            "  /  O    O  \\  ",
            " |            | ",
            " |     __     | ",
            " |    /  \\    | ",
            "  \\   \\__/   /  ",
            "   \\________/   ",
            "      ||||      ",
            "      ||||      ",
            "     /    \\     ",
            "    /      \\    ",
            "   /        \\   ",
            "  /__      __\\  ",
            "     |    |     ",
            "     |____|     "
        ],
        "happy": [
            "    ________    ",
            "   /        \\   ",
            "  /  ^    ^  \\  ",
            " |            | ",
            " |            | ",
            " |   \\____/   | ",
            "  \\          /  ",
            "   \\________/   ",
            "      ||||      ",
            "      ||||      ",
            "     /    \\     ",
            "    /      \\    ",
            "   /        \\   ",
            "  /__      __\\  ",
            "     |    |     ",
            "     |____|     "
        ],
        "cool": [
            "    ________    ",
            "   /        \\   ",
            "  / [##][##] \\  ",
            " |            | ",
            " |     __     | ",
            " |    |  |    | ",
            "  \\    --    /  ",
            "   \\________/   ",
            "      ||||      ",
            "      ||||      ",
            "     /    \\     ",
            "    /      \\    ",
            "   /        \\   ",
            "  /__      __\\  ",
            "     |    |     ",
            "     |____|     "
        ],
        "robot": [
            "  ____________  ",
            " |  []    []  | ",
            " |            | ",
            " |   ______   | ",
            " |  |______|  | ",
            " |____________| ",
            "    |      |    ",
            "   _|      |_   ",
            "  |          |  ",
            "  |   ____   |  ",
            "  |  |    |  |  ",
            "  |  |    |  |  ",
            "  |__|    |__|  ",
            "   ||      ||   ",
            "   ||      ||   ",
            "  [__]    [__]  "
        ],
        "cat": [
            " /\\___/\\        ",
            "(  o.o  )       ",
            " > ^ <          ",
            "/|   |\\         ",
            " |   |          ",
            " |___|          ",
            "  | |           ",
            "  | |           ",
            " _| |_          ",
            "|_____|         ",
            "                ",
            "                ",
            "                ",
            "                ",
            "                ",
            "                "
        ],
        "star": [
            "       *        ",
            "      ***       ",
            "     *****      ",
            "    *******     ",
            "   *********    ",
            "  ***********   ",
            " ************* ",
            "***************",
            " ************* ",
            "  ***********   ",
            "   *********    ",
            "    *******     ",
            "     *****      ",
            "      ***       ",
            "       *        ",
            "                "
        ],
        "heart": [
            "                ",
            "  ***     ***   ",
            " *****   ***** ",
            "*************  ",
            "*************  ",
            " ***********   ",
            "  *********    ",
            "   *******     ",
            "    *****      ",
            "     ***       ",
            "      *        ",
            "                ",
            "                ",
            "                ",
            "                ",
            "                "
        ],
        "ninja": [
            "   __________   ",
            "  |__________|  ",
            "  | >    < |   ",
            "  |________|   ",
            "     |  |       ",
            "    /|  |\\      ",
            "   / |  | \\     ",
            "  |  |  |  |    ",
            "  |  |  |  |    ",
            "  |  |  |  |    ",
            "  |__|  |__|    ",
            "   ||    ||     ",
            "   ||    ||     ",
            "  [__]  [__]    ",
            "                ",
            "                "
        ]
    }

    @staticmethod
    def get_avatar_list() -> List[dict]:
        """Get list of available avatars with names"""
        return [
            {"name": "Default", "key": "default"},
            {"name": "Happy", "key": "happy"},
            {"name": "Cool", "key": "cool"},
            {"name": "Robot", "key": "robot"},
            {"name": "Cat", "key": "cat"},
            {"name": "Star", "key": "star"},
            {"name": "Heart", "key": "heart"},
            {"name": "Ninja", "key": "ninja"}
        ]

    @staticmethod
    def get_avatar(key: str) -> List[str]:
        """Get avatar by key"""
        return ProfilePicture.AVATARS.get(key, ProfilePicture.AVATARS["default"])

    @staticmethod
    def display_avatar(avatar_lines: List[str], color: str = "white") -> str:
        """Format avatar for display with color"""
        return "\n".join([f"[{color}]{line}[/{color}]" for line in avatar_lines])

    @staticmethod
    def get_avatar_mini(key: str) -> str:
        """Get a mini 2x2 representation of avatar for chat"""
        mini_avatars = {
            "default": "😀",
            "happy": "😊",
            "cool": "😎",
            "robot": "🤖",
            "cat": "🐱",
            "star": "⭐",
            "heart": "❤️",
            "ninja": "🥷"
        }
        return mini_avatars.get(key, "👤")
