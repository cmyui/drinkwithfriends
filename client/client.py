from typing import List, Tuple, Optional, Union
from socket import socket, AF_INET, SOCK_STREAM, error as sock_err
from sys import exit
from time import sleep
from re import match as re_match
from numpy import arange # float range() function
#from bcrypt import hashpw, gensalt
from random import randint

from objects import glob

from common.objects.user import User
from common.objects.bottle import Bottle
from common.objects.inventory import Inventory
from common.constants import dataTypes, packets, privileges
from common.helpers.packetHelper import Packet, Connection
#from objects import glob # not yet needed

from colorama import init as clr_init, Fore as colour
clr_init(autoreset=True)

class Client:
    def __init__(self, start_loop: bool = False, debug: bool = False):
        """ Client Information. """
        self.version = 100
        self.debug = debug

        """ User information (our client user). """
        self.user = User() # User object for the player. Will be used if playing online.
        self.inventory = Inventory([]) # Our user's inventory. Will be used if playing online.

        self.online_users: List[User] = [] # A list of online users connected to the server. Inclues our user.

        """ Start up the game loop. """
        print(f'[CLNT] {colour.LIGHTBLUE_EX}Drink with Friends v{self.version / 100:.2f}\n')
        if start_loop:
            self._gameLoop()

        return

    @property
    def is_online(self) -> bool:
        return self.user and self.user.id

    def __del__(self) -> None: # If we're logged in, log out before closing.
        if self.is_online:
            self.make_request(packets.client_logout)
        print('Thanks for playing! <3')
        return

    def _gameLoop(self) -> None:
        while True:
            self.print_main_menu()

            choice_count: int = 2
            if self.is_online:
                if self.user.privileges & privileges.USER_PERMS:  choice_count += 5 # 6 with ledger
                if self.user.privileges & privileges.ADMIN_PERMS: choice_count += 2

            choice: int = self.get_user_int(0, choice_count)

            if not choice: break # Exit

            if not self.is_online: # *** Not logged in. ***
                if   choice == 1: # Login
                    self.make_request(packets.client_login)
                    if not self.is_online: continue # failed to login
                    self.make_request(packets.client_getInventory)
                elif choice == 2: # Register
                    self.make_request(packets.client_registerAccount)
            else: # *** Logged in. ***
                if   choice == 1: # Logout
                    self.make_request(packets.client_logout)
                elif choice == 2: # Request online users list.
                    self.make_request(packets.client_getOnlineUsers)
                    self.print_online_users()
                elif choice == 3: # Add a bottle to inventory.
                    self.make_request(packets.client_addBottle)
                    self.make_request(packets.client_getInventory)
                elif choice == 4: # Display your inventory.
                    print(self.inventory)
                elif choice == 5: # Take a shot
                    if self.inventory.is_empty:
                        print(
                            'Your inventory is empty!',
                            'How are you supposed to take a shot? x('
                        )
                        continue

                    self.make_request(packets.client_takeShot)
                elif choice == 6: pass # Check your ledger.

                # Admin
                elif choice == 7: pass # Ban user?
                elif choice == 8: pass # Shutdown server?
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
            username: str = input('Username: ') # newline to space from menu
            password: str = input('Password: ')
            packet.pack_data([
                [username, dataTypes.STRING],
                [password, dataTypes.STRING],
                [self.version, dataTypes.INT16]
            ])
            del password

            sock.send(packet.get_data())
            del packet

            resp: int = ord(sock.recv(1))

            if resp == packets.server_generalSuccess:
                print(f'{colour.LIGHTGREEN_EX}Authenticated.')

                try: conn = Connection(sock.recv(glob.max_bytes))
                except:
                    print('Connection died - server_generalSuccess.')
                    del resp, username
                    return

                with Packet() as packet:
                    packet.read_data(conn.body)
                    self.user.id, self.user.privileges = packet.unpack_data([dataTypes.INT16, dataTypes.INT16])#[0]
                    self.online_users = [User(u[1], u[0], u[2]) for u in packet.unpack_data([dataTypes.USERINFO_LIST])]

                self.user.username = username

                self.print_online_users()

            elif resp == packets.server_generalFailure:
                print(f'{colour.LIGHTRED_EX}Invalid login parameters.')
            elif resp == packets.server_generalNoSuchUsername:
                print(f'{colour.LIGHTRED_EX}No such username found.')
            elif resp == packets.server_generalIncorrectPassword:
                print(f'{colour.LIGHTRED_EX}Incorrect password.')
            elif resp == packets.server_generalBanned:
                print(f'{colour.LIGHTRED_EX}Your account has been banned.')
            else: print(f'{colour.LIGHTRED_EX}Invalid packetID {resp}')
            #input('Press enter to continue..')
            #print('\033[F', ' ' * 25, sep='') # lol i should just make a function for wiping lines already..
            del resp, username
            return
        elif packet.id == packets.client_logout:
            print(f'{colour.YELLOW}Logging out..')
            packet.pack_data([[self.user.id, dataTypes.INT16]])
            sock.send(packet.get_data())
            del packet
            self.user.__del__()
            return
        elif packet.id == packets.client_getOnlineUsers:
            sock.send(packet.get_data())
            del packet

            try: conn = Connection(sock.recv(glob.max_bytes)) # TODO: with conn
            except:
                print('Connection died - client_getOnlineUsers.')
                return

            with Packet() as packet:
                packet.read_data(conn.body)
                resp: Tuple[Union[int, str]] = packet.unpack_data([dataTypes.USERINFO_LIST])
                if len(resp) != 1: return # TODO: response
                if (x for x in (_x[1] for _x in resp) if x not in (u.username for u in self.online_users)):
                    self.online_users = [User(u[1], u[0], u[2]) for u in resp]
                del resp
        elif packet.id == packets.client_registerAccount:
            print(
                'Registration',
                '------------',
                f'{colour.RED}NOTE: currently in plaintext, do not use a real password!\n'
            )
            username: str = self.get_user_str_lenrange('Username: ', 3, 16)
            password: str = self.get_user_str_lenrange('Password: ', 6, 32)
            packet.pack_data([
                [username, dataTypes.STRING],
                [password, dataTypes.STRING]
            ])
            sock.send(packet.get_data())
            del packet

            resp: int = ord(sock.recv(1))
            if resp == packets.server_generalSuccess:
                print(f'{colour.LIGHTGREEN_EX}Account successfully created.')
            elif resp == packets.server_registrationUsernameTaken:
                print(f'{colour.LIGHTRED_EX}That username is already taken!')
            elif resp == packets.server_generalFailure:
                print(f'{colour.LIGHTRED_EX}Invalid parameters.')
            del username, password
        elif packet.id == packets.client_addBottle:
            print(
                'Add bottle to inventory',
                '-----------------------',
                sep='\n'
            )
            b = Bottle(
                self.get_user_str_lenrange(1, 32, 'Bottle name: '),
                self.get_user_int(50, 5000, 'ml: '),
                self.get_user_float(1.0, 100.0, 'ABV: ')
            )
            packet.pack_data([
                [self.user.id, dataTypes.INT16],
                [[b.name, b.volume, b.abv], dataTypes.DRINK]
            ])
            sock.send(packet.get_data())
            del packet

            resp: int = ord(sock.recv(1))
            if resp == packets.server_generalSuccess:
                self.inventory += b
                # TODO: nice print function for inventory
                print(f'\n{colour.LIGHTBLUE_EX}Added a bottle to your inventory.\n{self.inventory}\n')
            elif resp == packets.server_generalFailure:
                print(f'{colour.LIGHTRED_EX}Server failed to add bottle to database.')
            del b
        elif packet.id == packets.client_getInventory:
            #print(f'{colour.YELLOW}Requesting inventory from server..')
            packet.pack_data([[self.user.id, dataTypes.INT16]]) # UserID
            sock.send(packet.get_data())
            del packet

            try: conn = Connection(sock.recv(glob.max_bytes)) # TODO: with conn
            except:
                print('Connection died - client_getInventory.')
                return

            with Packet() as packet:
                packet.read_data(conn.body)
                resp = packet.unpack_data([dataTypes.DRINK_LIST])

            self.inventory = Inventory([Bottle(*b) for b in resp])
        elif packet.id == packets.client_takeShot:
            if self.get_user_bool('Would you like to choose your drink?\n>> '):
                print(self.inventory)
                b = self.inventory.get_bottle(self.get_user_int(1, len(self.inventory.bottles)))
            else:
                b = self.inventory.get_bottle(randint(1, len(self.inventory.bottles)))

            # TODO: add choice for amt?
            vol: int = randint(30, 85) # 40.5ml = standard shot
            if vol > b.volume: vol = b.volume

            # Send to server to update inventory
            packet.pack_data([
                [self.user.id, dataTypes.INT16],
                [[b.name, b.volume, b.abv], dataTypes.DRINK]
            ])
            sock.send(packet.get_data())
            del packet

            resp: int = ord(sock.recv(1))
            if resp == packets.server_generalFailure:
                print(
                    'An error occurred while syncing with the server.',
                    'The shot has not been subtracted from your bottle due to this error.'
                )
                return

            print(
                "\nHere's what the doctor ordered:",
                f'Drink:  {b.name} [{b.abv}%]',
                f'Volume: {vol}ml [~{vol * b.abv:.0f} cmynts] ({(vol / b.volume) * 100:.0f}% of bottle)',
                'Bottoms up!', sep='\n'
            )

            b.volume -= vol

            if not b.volume: # finished the bottle
                print(f"{colour.YELLOW}You've finished your {b.name}!")
                self.inventory -= b
        else:
            print(f'{colour.YELLOW}[WARN] Unfinished packet.')
            input(f'{colour.MAGENTA}Waiting for user input to continue..')
        return

    @staticmethod
    def get_user_str_lenrange(min: int, max: int, message: Optional[str] = None) -> str: # ugly name but what else??
        """
        Get a string with the length in range min-max (inclusive) from stdin.
        """
        while True:
            tmp: str = input(message if message else '>')
            if len(tmp) in range(min, max + 1): return tmp
            # TODO: print backspace to clean up previous failures? keep menu on screen..
            print(f'{colour.LIGHTRED_EX}Input string must be between {min}-{max} characters.')

    @staticmethod
    def get_user_int(min: int, max: int, message: Optional[str] = None) -> int:
        """
        Get a single integer in range min-max (inclusive) from stdin.
        """
        while True:
            tmp: str = input(message if message else '> ')
            if re_match(r'^-?\d+$', tmp) and int(tmp) in range(min, max + 1): return int(tmp)
            # TODO: print backspace to clean up previous failures? keep menu on screen..
            print(f'{colour.LIGHTRED_EX}Please enter a valid value.')

    @staticmethod
    def get_user_float(min: float, max: float, message: Optional[str] = None) -> float:
        """
        Get a single float in range min-max (inclusive) from stdin.
        """
        while True:
            tmp: str = input(message if message else '> ')
            if re_match(r'^-?\d+(?:\.\d+)?$', tmp) and float(tmp) in arange(min, max + 1): return float(tmp)
            # TODO: print backspace to clean up previous failures? keep menu on screen..
            print(f'{colour.LIGHTRED_EX}Please enter a valid value.')

    @staticmethod
    def get_user_bool(message: Optional[str] = None) -> bool:
        """
        Get a bool from stdin (message must contain 'y' and not contain 'n').
        """
        while True:
            tmp: str = input(message if message else '> ')
            if not re_match(r'^(?:y|n)(?:.*)$', tmp):
                print(f'{colour.LIGHTRED_EX}Please enter a valid value.')
                continue
            return tmp.startswith('y')
            # TODO: print backspace to clean up previous failures? keep menu on screen..

    def print_main_menu(self) -> None:
        print('', # Print a space at the top of menu.
            f'{colour.CYAN}<- {colour.YELLOW}Main Menu {colour.CYAN}->',
            '0. Exit',
            sep='\n'
        )

        if not self.is_online: # *** Not logged in. ***
            print(
                '1. Login',
                '2. Register an account.',
                sep='\n'
            )
        else: # *** Logged in. ***
            print(
                '1. Logout',
                '2. List online users.',
                '3. Add bottle.',
                '4. Display your inventory',
                '5. Take a shot.',
                #'6. Check your ledger.',
                sep='\n'
            )

            # Just ideas, not finished.
            #if self.user.privileges & privileges.ADMIN_PERMS: print(
            #    '7. Kick user.',
            #    '8. Ban user.',
            #    '9. Restart server.',
            #    '10. Shutdown server.', sep='\n'
            #)

        print() # Print an extra space at the end of the menu
        return

    def print_online_users(self) -> None:
        print(f'\n{colour.CYAN}<- {colour.YELLOW}Online Users {colour.CYAN}->')
        for u in self.online_users: print(f'{u.id} - {u.username}.')
        #print('')
        return

if __name__ == '__main__':
    Client(True, input('Launch in debug?\n>> ').startswith('y'))
