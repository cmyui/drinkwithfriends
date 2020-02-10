import socket
from sys import exit

from common.constants import dataTypes
from common.constants import packetID


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

    try: s.connect(('51.79.17.191', 6999))
    except socket.error as err:
        print(f'Failed to establish a connection to the server:\n{err}')
        exit(1)

    print('Connection established.')
    s.send(Packet(packetID.client_login).get_data)
    s.close()
    exit(0)
