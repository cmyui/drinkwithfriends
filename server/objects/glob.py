from typing import Any, Optional
from mysql.connector.pooling import MySQLConnectionPool
from time import time

start_time: float = time()

db: Optional[MySQLConnectionPool] = None
config: Optional[Any] = None
debug: bool = False
