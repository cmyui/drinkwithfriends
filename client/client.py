import socket
from sys import exit
from time import sleep
#from bcrypt import hashpw, gensalt

from common.constants import dataTypes
from common.constants import packetID
from common.helpers.packetHelper import Packet
#from objects import glob # not yet needed

global _version
_version = 100

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

    try: s.connect(('51.79.17.191', 6999))
    except socket.error as err:
        print(f'Failed to establish a connection to the server: {err}.')
        exit(1)

    print('Connection established.')

    while True: # Loop until they login
        print('Attempting to login to the server..')
        p = Packet(packetID.client_login)
        p.pack_data((
            (input('Username: '), dataTypes.STRING),
            (input('Password: '), dataTypes.STRING),
            #(hashpw(input('Password: '), gensalt()), dataTypes.STRING), # TODO: maybe use?
            (_version, dataTypes.UINT)
        ))

        s.send(p.get_data)
        resp = ord(s.recv(1))

        if resp == packetID.server_loginInvalidData:
            print('Invalid credential format.') # TODO: give credential format..
        elif resp == packetID.server_loginNoSuchUsername:
            print('No such username found.')
        elif resp == packetID.server_loginIncorrectPassword:
            print('Incorrect password.')
        elif resp == packetID.server_loginBanned:
            print('Your account has been banned.')
            exit(1) # Rest in peace.
        elif resp == packetID.server_loginSuccess:
            print('Authenticated.')
            break
        else:
            print(f'Invalid packetID {resp}')
            exit(1)


    s.close()
    #exit(0)

print('Connection closed.')
