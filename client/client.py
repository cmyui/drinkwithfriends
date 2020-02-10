import socket
from sys import exit

HOST: str = r'https://cmyui.codes/dwf/'

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

try: sock.connect(HOST)
except socket.error as err:
    print(err)
    exit(1)

print('success')
sock.send(b'\x01')
sock.close()
exit(0)
