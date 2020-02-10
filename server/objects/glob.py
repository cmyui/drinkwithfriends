from typing import Any, List, Optional
from mysql.connector.pooling import MySQLConnectionPool
from time import time

from common.objects.user import User

start_time: float = time()

users: List[User] = []

db: Optional[MySQLConnectionPool] = None
config: Optional[Any] = None
debug: bool = False
