class User(object):
    def __init__(self, username: str, client_password: str, game_version: int = 0) -> None:
        self.username = username
        self.client_password = client_password
        self.db_password = ''

        self.username_safe = self.safe_username(self.username)
        self.game_version = game_version
        return

    @staticmethod
    def safe_username(username: str) -> str:
        return username.replace(' ', '_').strip()
