from typing import List, Optional
from socket import socket, AF_INET, SOCK_STREAM, error as sock_err
from sys import exit
from time import sleep
#from bcrypt import hashpw, gensalt

from objects import glob

from common.objects.user import User
from common.constants import dataTypes
from common.constants import packets
from common.helpers.packetHelper import Packet, Connection
#from objects import glob # not yet needed

global _version
_version = 100

class Client(object):
    def __init__(self, start_loop: bool = False):
        self.user = None

        self.online_users: List[int] = []

        if start_loop:
            self._handle_connections()

    def _handle_connections(self) -> None:
        while True:
            with socket(AF_INET, SOCK_STREAM) as s:
                self.handle_connection(s)
        return

    def handle_connection(self, sock: socket) -> None:
        try: sock.connect((glob.ip, glob.port))
        except sock_err as err:
            print(f'Failed to establish a connection to the server: {err}.')
            return

        # Connection established
        if not self.user: # Login
            p = Packet(packets.client_login)

            username: str = input('Username: ')
            password: str = input('Password: ')
            p.pack_data([
                (username, dataTypes.STRING),
                (password, dataTypes.STRING),
                (_version, dataTypes.UINT32)
            ])

            sock.send(p.get_data)
            del p

            resp = ord(sock.recv(1))
            print('Failed to recieve value from server.')
            return

            if resp == packets.server_loginInvalidData:
                print('Invalid login data.')
            elif resp == packets.server_loginNoSuchUsername:
                print('No such username found.')
            elif resp == packets.server_loginIncorrectPassword:
                print('Incorrect password.')
            elif resp == packets.server_loginBanned:
                print('Your account has been banned.')
            elif resp == packets.server_loginSuccess:
                print('Authenticated.')

                conn = Connection(sock.recv(glob.max_bytes))
                print(conn.body)

                p = Packet()
                p.read_data(conn.body)
                print(p.__dict__)

                print(p.unpack_data(( # pylint: disable=unbalanced-tuple-unpacking
                    dataTypes.UINT16,
                    dataTypes.INT_LIST
                )))

                self.user = User(id, username, _version)

                print(f'self.online_users: {self.online_users}')
            else: print(f'Invalid packetID {resp}')
            return
        else: print('how did i get here?')

if __name__ == '__main__':
    Client(True)

print('Thanks for playing! <3')
