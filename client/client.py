from typing import List, Optional
from socket import socket, AF_INET, SOCK_STREAM, error as sock_err
from sys import exit
from time import sleep
#from bcrypt import hashpw, gensalt

from objects import glob

from common.objects.user import User
from common.constants import dataTypes, packets, privileges
from common.helpers.packetHelper import Packet, Connection
#from objects import glob # not yet needed

from colorama import init as clr_init, Fore as colour
clr_init(autoreset=True)

global _version
_version = 100

class Client(object):
    def __init__(self, start_loop: bool = False):
        self.user = User()
        self.version = 100

        self.online_users: List[int] = []

        if start_loop:
            self.gameloop()
            #self._handle_connections()

    def __del__(self):
        if self.user.id: # If we're logged in, log out before closing.
            self.make_request(packets.client_logout)
        print('Thanks for playing! <3')

    def gameloop(self) -> None:
        while True:
            self.print_main_menu()
            choice: int = self.get_user_int(1, 10)

            # TODO: constants with menu option names?

            # User
            if choice == 1: self.make_request(packets.client_logout if self.user.id else packets.client_login) # Login / Logout.
            elif choice == 2: pass # Check global leaderboards.
            elif choice == 3: pass # List online users.
            elif choice == 4: pass # Check your ledger.

            # Mod
            elif choice == 5: pass # Silence user.
            elif choice == 6: pass # Check silence list.

            # Admin
            elif choice == 7: pass # Kick user.
            elif choice == 8: pass # Ban user.
            elif choice == 9: pass # Restart server.
            elif choice == 10: pass # Shutdown server.

        return

    #def _handle_connections(self) -> None:
    #    while True:
    #        with socket(AF_INET, SOCK_STREAM) as s:
    #            self.handle_connection(s)
    #    return

    def make_request(self, packetID: int) -> None:
        with socket(AF_INET, SOCK_STREAM) as sock:
            try: sock.connect((glob.ip, glob.port))
            except sock_err as err:
                print(f'Failed to establish a connection to the server: {err}.')
                return

            # We've established a valid connection.
            packet = Packet(packetID)
            self._handle_connection(sock, packet)
        return


    def _handle_connection(self, sock: socket, packet: Packet) -> None:

        if packet.id == packets.client_login:
            #p = Packet(packets.client_login)

            username: str = input('Username: ')
            password: str = input('Password: ')
            packet.pack_data([
                (username, dataTypes.STRING),
                (password, dataTypes.STRING),
                (self.version, dataTypes.INT16)
            ])

            sock.send(packet.get_data())
            del packet

            resp: int = ord(sock.recv(1))

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

                packet = Packet()
                packet.read_data(conn.body)

                self.user.id, self.online_users = packet.unpack_data(( # pylint: disable=unbalanced-tuple-unpacking
                    dataTypes.INT16,
                    dataTypes.INT16_LIST
                ))

                del packet

                self.user.username = username
                self.user._safe_username()

                print(f'Online users: {self.online_users}')
            else: print(f'Invalid packetID {resp}')
            return
        elif packet.id == packets.client_logout:
            print('Logging out..')
            packet.pack_data([
                (self.user.id, dataTypes.INT16)
            ])
            sock.send(packet.get_data())
            del packet
            self.user.__del__()
            return
        else:
            print('[WARN] Unfinished packet.')
            input()

    @staticmethod
    def get_user_int(min: int, max: int) -> int:
        """
        Get a single integer in range min-max (inclusive) from stdin.
        """
        while True:
            tmp: str = input('> ')
            if tmp.isdecimal() and int(tmp) >= min and int(tmp) <= max: # TODO: maybe not?
                return int(tmp)

            # TODO: print backspace to clean up previous failures? keep menu on screen..

            print(f'{colour.LIGHTRED_EX}Please enter a valid value.')

    def print_main_menu(self) -> None:
        print(
            f'[CLNT] {colour.LIGHTBLUE_EX}Drink with Friends v{self.version / 100:.2f}\n',
            '<- Main Menu ->',
            f'1. {"Logout" if self.user.id else "Login"}', sep='\n'
        )
        if self.user.id:
            print(
                '2. Check global leaderboards.',
                '3. List online users.',
                '4. Check your ledger.', sep='\n'
            )
        if self.user.privileges & privileges.MOD_PERMS:
            print(
                '5. Silence user.',
                '6. Check silence list.', sep='\n'
            )
        if self.user.privileges & privileges.ADMIN_PERMS:
            print(
                '7. Kick user.',
                '8. Ban user.',
                '9. Restart server.',
                '10. Shutdown server.', sep='\n'
            )
        return

if __name__ == '__main__':
    Client(start_loop = True)
