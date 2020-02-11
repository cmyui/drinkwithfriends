from typing import Any, List, Optional
from mysql.connector.pooling import MySQLConnectionPool
from time import time

from common.objects.user import User

start_time: float = time()

users: List[User] = [
    User(51, 'senor', 1, 100),
    User(432, 'ds', 0, 100),
    User(12, 'hth', 8, 100),
    User(5, 'yes', 1, 100),
    User(32, 'yeahahe', 1, 100)
]

db: Optional[MySQLConnectionPool] = None
config: Optional[Any] = None
debug: bool = False
