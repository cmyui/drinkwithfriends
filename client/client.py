import socket
from sys import exit

from common.constants import dataTypes
from common.constants import packetID
from common.helpers.packetHelper import Packet
#from objects import glob # not yet needed

global _version
_version = 100

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

    try: s.connect(('51.79.17.191', 6999))
    except socket.error as err:
        print(f'Failed to establish a connection to the server:\n{err}')
        exit(1)

    print('Connection established.')

    # Login
    print('Attempting to login to the server..')
    p = Packet(packetID.client_login)
    p.pack_data((
        ('cmyui', dataTypes.STRING), # Username
        (_version, dataTypes.UINT) # Game version
    ))

    s.send(p.get_data)

    data = s.recv(1)
    if data: print(f'success - {data}')
    else: print(f'failure - {data}')


    s.close()
    exit(0)
