from typing import List, Tuple, Optional, Union
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

class Client(object):
    def __init__(self, start_loop: bool = False):
        self.user = User()
        self.version = 100

        self.online_users: List[User] = []

        if start_loop:
            self._gameLoop()

        return

    @property
    def is_online(self) -> bool:
        return self.user and self.user.id

    def __del__(self) -> None:
        if self.is_online: # If we're logged in, log out before closing.
            self.make_request(packets.client_logout)
        print('Thanks for playing! <3')
        return

    def _gameLoop(self) -> None:
        while True:

            self.print_main_menu()
            choice: int = self.get_user_int(0, 10)

            # TODO: constants with menu option names?

            # User
            if not choice: return
            elif choice == 1:
                self.make_request(packets.client_logout if self.is_online else packets.client_login) # Login / Logout.
                continue
            if self.is_online:
                if choice == 2: # Check global leaderboards.
                    pass
                elif choice == 3:
                    self.make_request(packets.client_getOnlineUsers)
                    self.print_online_users() # List online users.
                    continue
                elif choice == 4: # Check your ledger.
                    pass

                # Mod
                elif choice == 5: # Silence user.
                    pass
                elif choice == 6: # Check silence list.
                    pass

                # Admin
                elif choice == 7: # Kick user.
                    pass
                elif choice == 8: # Ban user.
                    pass
                elif choice == 9: # Restart server.
                    pass
                elif choice == 10: # Shutdown server.
                    pass

        return


    def make_request(self, packetID: int) -> None:
        with socket(AF_INET, SOCK_STREAM) as sock:
            try: sock.connect((glob.ip, glob.port))
            except sock_err as err:
                print(f'{colour.LIGHTRED_EX}Failed to establish a connection to the server: {err}.\n')
                return

            # We've established a valid connection.
            with Packet(packetID) as packet:
                self._handle_connection(sock, packet)

        return


    def _handle_connection(self, sock: socket, packet: Packet) -> None:

        if packet.id == packets.client_login:
            username: str = input('\nUsername: ') # newline to space from menu
            password: str = input('Password: ')
            packet.pack_data([
                [username, dataTypes.STRING],
                [password, dataTypes.STRING],
                [self.version, dataTypes.INT16]
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

                self.user.id = packet.unpack_data([dataTypes.INT16])[0]
                #print(f'\n\n{[u for u in packet.unpack_data([dataTypes.USERINFO_LIST])]}\n\n')
                resp = packet.unpack_data([dataTypes.USERINFO_LIST])
                print(resp)
                self.online_users = [User(*u) for u in resp]
                del packet

                self.user.username = username
                #self.user._safe_username()

                #print('Online users:', f'{", ".join(u.username for u in self.online_users)}.')
                self.print_online_users()
            else: print(f'Invalid packetID {resp}')
            return
        elif packet.id == packets.client_logout:
            print('Logging out..')
            packet.pack_data([[self.user.id, dataTypes.INT16]])
            sock.send(packet.get_data())
            del packet
            self.user.__del__()
            return
        elif packet.id == packets.client_getOnlineUsers:
            sock.send(packet.get_data())
            del packet

            conn = Connection(sock.recv(glob.max_bytes)) # TODO: with conn
            with Packet() as packet:
                packet.read_data(conn.body)
                resp: Tuple[Union[int, str]] = packet.unpack_data([dataTypes.USERINFO_LIST])
                _t = [x for x in [_x[1] for _x in resp] if x not in [u.username for u in self.online_users]] # lmao
                if _t: # TODO: logouts
                    print(f'Login: {", ".join(_t)}.')
                    self.online_users = [User(*u) for u in resp]
                del resp, _t
                #if list(filter(lambda u: u.id not in ))
                #self.online_users = [User(*u) for u in packet.unpack_data([dataTypes.USERINFO_LIST])]
                #_online = packet.unpack_data([dataTypes.USERINFO_LIST])[0]
                #changes = list(filter(lambda u: u not in _online, self.online_users))
                #if changes: print(f'Login: {", ".join(changes)}.')
                #self.online_users = _online
                #del _online, changes
        elif packet.id == packets.client_addBottle:
            pass
        else:
            print('[WARN] Unfinished packet.')
            input()

        return

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
            '0. Exit',
            f'1. {"Logout" if self.is_online else "Login"}', sep='\n'
        )
        if self.is_online:
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

    def print_online_users(self) -> None:
        print('\n<- Online Users ->')
        for u in self.online_users: print(f'{u.id} - {u.username}.')
        print('')
        return

if __name__ == '__main__':
    Client(start_loop = True)
