from typing import Tuple
import socket
from sys import exit

HOST: Tuple[str] = ('51.79.17.191', 6999)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try: sock.connect(HOST)
except socket.error as err:
    print(err)
    exit(1)

print('success')
sock.send(b'\x01')
sock.close()
exit(0)
