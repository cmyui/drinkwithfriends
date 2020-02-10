from typing import Optional

class User(object):
    def __init__(self, id: Optional[int] = None, username: str = '', privileges: int = 0, game_version: int = 0) -> None:
        self.id = id
        self.username = username
        self.privileges = privileges
        self.db_password = ''

        self.username_safe = self.safe_username(self.username)
        self.game_version = game_version
        return

    @staticmethod
    def safe_username(username: str) -> str:
        return username.replace(' ', '_').strip()
