from typing import Optional

class User(object):
    def __init__(self, id: int = 0, username: str = '', privileges: int = 0) -> None:
        self.id = id
        self.username = username
        self.username_safe = self.safe_username(self.username)
        self.privileges = privileges
        return

    def __del__(self) -> None: # Logout
        self.id = 0
        self.username = ''
        #del self.username_safe
        self.privileges = 0
        return

    @staticmethod
    def safe_username(username: str) -> str:
        return username.replace(' ', '_').strip()

    def _safe_username(self) -> None:
        self.username_safe = self.safe_username(self.username)
        return
