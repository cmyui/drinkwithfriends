from typing import List, Tuple, Optional, Union
from socket import socket, AF_INET, SOCK_STREAM, error as sock_err
from sys import exit, stdout
from time import sleep, time
from re import match as re_match
from numpy import arange # float range() function
#from bcrypt import hashpw, gensalt
from random import randint
from getpass import getpass

from objects import glob

from common.objects.user import User
from common.objects.bottle import Bottle
from common.objects.inventory import BottleCollection
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

        self.lines_printed = 0

        """ User information (our client user). """
        self.user = User() # User object for the player. Will be used if playing online.
        self.inventory = BottleCollection('Inventory', []) # Our user's inventory. Will be used if playing online.
        self.ledger = BottleCollection('Ledger', [])
        self.ledger.unit = 'shots'

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
                if self.user.privileges & privileges.USER_PERMS:  choice_count += 6
                if self.user.privileges & privileges.ADMIN_PERMS: choice_count += 2

            choice: int = self.get_user_int(0, choice_count)

            if not choice: break # Exit

            self.move_cursor_up(1 + choice_count + self.lines_printed, 43)
            self.lines_printed = 0

            if not self.is_online: # *** Not logged in. ***
                if   choice == 1: # Login
                    self.make_request(packets.client_login)
                    if not self.is_online: continue # failed to login

                    self.log_debug('Getting inventory.')
                    self.make_request(packets.client_getInventory)
                    self.log_debug('Getting ledger.')
                    self.make_request(packets.client_getLedger)
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
                    self.inventory.display()
                    self.lines_printed += (self.inventory.bottles.__len__() + 2 if self.inventory.bottles else 3)
                elif choice == 5: # Take a shot
                    if self.inventory.is_empty:
                        print(
                            'Your inventory is empty!',
                            'How are you supposed to take a shot? x('
                        )
                        continue

                    self.make_request(packets.client_takeShot)
                    #self.make_request(packets.client_getLedger)
                elif choice == 6:
                    self.ledger.display() # Check your ledger.
                    self.lines_printed += (self.ledger.bottles.__len__() + 2 if self.ledger.bottles else 3)

                # Admin
                elif choice == 7: pass # Ban user?
                elif choice == 8: pass # Shutdown server?
        return

    def make_request(self, packetID: int) -> None:
        with socket(AF_INET, SOCK_STREAM) as sock:
            try: sock.connect((glob.ip, glob.port))
            except sock_err as err:
                self.log_error(f'Failed to establish a connection to the server: {err}.\n')
                return

            # We've established a valid connection.
            with Packet(packetID) as packet:
                self._handle_connection(sock, packet)
        return

    def _handle_connection(self, sock: socket, packet: Packet) -> None:
        if packet.id == packets.client_login:
            username: str = input('Username: ') # newline to space from menu
            password: str = getpass()
            print() # Print new line to split from.. everything

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
                self.log_info('Authenticated.')

                try: conn = Connection(sock.recv(glob.max_bytes))
                except:
                    self.log_error('Connection died - server_generalSuccess.')
                    del resp, username
                    return

                with Packet() as packet:
                    packet.read_data(conn.body)
                    self.user.id, self.user.privileges = packet.unpack_data([dataTypes.INT16, dataTypes.INT16])#[0]
                    self.online_users = [User(u[1], u[0], u[2]) for u in packet.unpack_data([dataTypes.USERINFO_LIST])]

                self.user.username = username

                self.print_online_users()

            elif resp == packets.server_generalFailure:
                self.log_error('Invalid login parameters.')
            elif resp == packets.server_generalNoSuchUsername:
                self.log_error('No such username found.')
            elif resp == packets.server_generalIncorrectPassword:
                self.log_error('Incorrect password.')
            elif resp == packets.server_generalBanned:
                self.log_error('Your account has been banned.')
            else: self.log_error(f'Invalid packetID {resp}')
            #input('Press enter to continue..')
            #print('\033[F', ' ' * 25, sep='') # lol i should just make a function for wiping lines already..
            del resp, username
            return
        elif packet.id == packets.client_logout:
            self.log_info('Logging out..', colour.YELLOW)
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
                self.log_error('Connection died - client_getOnlineUsers.')
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
                f'{colour.RED}NOTE: currently in plaintext, do not use a real password!\n',
                sep='\n'
            )
            username: str = self.get_user_str_lenrange(3, 16, 'Username: ')
            password: str = self.get_user_str_lenrange(6, 32, 'Password: ')
            packet.pack_data([
                [username, dataTypes.STRING],
                [password, dataTypes.STRING]
            ])
            sock.send(packet.get_data())
            del packet

            resp: int = ord(sock.recv(1))
            if resp == packets.server_generalSuccess:
                self.log_error('Account successfully created.')
            elif resp == packets.server_registrationUsernameTaken:
                self.log_error('That username is already taken!')
            elif resp == packets.server_generalFailure:
                self.log_error('Invalid parameters.')
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
                self.log_info(f'"{b.name}" has been added to your inventory.')
            elif resp == packets.server_generalFailure:
                self.log_error('Server failed to add bottle to database.')
            del b
        elif packet.id == packets.client_getInventory:
            #print(f'{colour.YELLOW}Requesting inventory from server..')
            packet.pack_data([[self.user.id, dataTypes.INT16]]) # UserID
            sock.send(packet.get_data())
            del packet

            resp: int = ord(sock.recv(1))
            if resp == packets.server_alreadyUpToDate:
                self.log
                return
            del resp

            try: conn = Connection(sock.recv(glob.max_bytes)) # TODO: with conn
            except:
                self.log_error('Connection died - client_getInventory.')
                return

            with Packet() as packet:
                packet.read_data(conn.body)
                resp = packet.unpack_data([dataTypes.DRINK_LIST])

            self.inventory = BottleCollection('Inventory', [Bottle(*b) for b in resp])
        elif packet.id == packets.client_takeShot:
            if self.get_user_bool('Would you like to choose your drink?\n>> '):
                self.inventory.display()
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
                self.log_error('An error has occurred while syncing with the server. Your inventory has not been modified.')
                return
            del resp

            print(
                "\nHere's what the doctor ordered:",
                f'Drink:  {b.name} [{b.abv}%]',
                f'Volume: {vol}ml [~{vol * b.abv:.0f} cmynts] ({(vol / b.volume) * 100:.0f}% of bottle)',
                'Bottoms up!', sep='\n'
            )
            self.lines_printed += 5

            b.volume -= vol
            self.ledger += b

            if not b.volume: # finished the bottle
                self.log_info(f"You've finished your {b.name}!", colour.YELLOW)
                self.inventory -= b
        elif packet.id == packets.client_getLedger:
            packet.pack_data([
                [self.user.id, dataTypes.INT16]
            ])
            sock.send(packet.get_data())
            del packet

            resp: int = ord(sock.recv(1))
            if resp == packets.server_alreadyUpToDate:
                return
            del resp

            try: conn = Connection(sock.recv(glob.max_bytes)) # TODO: with conn
            except:
                self.log_error('Connection died - client_getLedger.')
                return

            with Packet() as packet:
                packet.read_data(conn.body)
                resp = packet.unpack_data([dataTypes.DRINK_LIST])
            self.ledger = BottleCollection('Ledger', [Bottle(*b) for b in resp])
            self.ledger.unit = 'shots'
            del resp
        else: # Unknown packet ID.
            self.log_warn(f'Recieved an unknown packet. (ID: {packet.id})')
        return

    def get_user_str_lenrange(self, min: int, max: int, message: Optional[str] = None) -> str: # ugly name but what else??
        """
        Get a string with the length in range min-max (inclusive) from stdin.
        """
        while True:
            tmp: str = input(message if message else '>')
            if len(tmp) in range(min, max + 1): return tmp
            # TODO: print backspace to clean up previous failures? keep menu on screen..
            self.log_error(f'Input string must be between {min}-{max} characters.')

    def get_user_int(self, min: int, max: int, message: Optional[str] = None) -> int:
        """
        Get a single integer in range min-max (inclusive) from stdin.
        """
        while True:
            tmp: str = input(message if message else '> ')
            if re_match(r'^-?\d+$', tmp) and int(tmp) in range(min, max + 1): return int(tmp)
            # TODO: print backspace to clean up previous failures? keep menu on screen..
            self.log_error('Please enter a valid value.')

    def get_user_float(self, min: float, max: float, message: Optional[str] = None) -> float:
        """
        Get a single float in range min-max (inclusive) from stdin.
        """
        while True:
            tmp: str = input(message if message else '> ')
            if re_match(r'^-?\d+(?:\.\d+)?$', tmp) and float(tmp) in arange(min, max + 1): return float(tmp)
            # TODO: print backspace to clean up previous failures? keep menu on screen..
            self.log_error('Please enter a valid value.')

    def get_user_bool(self, message: Optional[str] = None) -> bool:
        """
        Get a bool from stdin (message must contain 'y' and not contain 'n').
        """
        while True:
            tmp: str = input(message if message else '> ')
            if not re_match(r'^(?:y|n)(?:.*)$', tmp):
                self.log_error('Please enter a valid value.')
                continue
            return tmp.startswith('y')

    def print_main_menu(self) -> None:
        print('', # Print a space at the top of menu.
            f'{colour.CYAN}<- {colour.YELLOW}Main Menu {colour.CYAN}->',
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
                '1. Logout       | 2. List online users.',
                '3. Add bottle.  | 4. Display your inventory',
                '5. Take a shot. | 6. Check your ledger.',
                sep='\n'
            )

            # Just ideas, not finished.
            #if self.user.privileges & privileges.ADMIN_PERMS: print(
            #    '7. Kick user.',
            #    '8. Ban user.',
            #    '9. Restart server.',
            #    '10. Shutdown server.', sep='\n'
            #)

        print('0. Exit.', end='\n\n')
        return

    def print_online_users(self) -> None:
        print(f'\n{colour.CYAN}<- {colour.YELLOW}Online Users {colour.CYAN}->')
        for u in self.online_users: print(f'{u.id} - {u.username}.')
        self.lines_printed += self.online_users.__len__() + 2
        return

    @staticmethod
    def move_cursor_up(count: int = 1, spaces: int = 0) -> None:
        for _ in range(count + 1):
            stdout.write('\033[F')
            if not spaces: continue
            stdout.write(' ' * spaces)
        if spaces: stdout.write('\r')
        return

    def log_info(self, message: str, col: int = colour.LIGHTBLUE_EX) -> None:
        self._print('[INFO]', message, col)
        return

    def log_warn(self, message: str) -> None:
        self._print('[WARN]', message, colour.YELLOW)
        return

    def log_error(self, message: str) -> None:
        self._print('[ERR]', message, colour.LIGHTRED_EX)
        return

    def log_debug(self, message: str) -> None:
        if self.debug:
            self._print('[DEBUG]', message, colour.LIGHTBLUE_EX)
        return

    def _print(self, prefix: str, message: str, col: int) -> None:
        print(f'[{prefix}] {col}{message}')
        for c in message: # add line for each \n found in message as well
            if c == '\n': self.lines_printed += 1
        self.lines_printed =+ 1
        return

if __name__ == '__main__':
    Client(True, False)#input('Launch in debug?\n>> ').startswith('y'))
