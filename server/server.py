# -*- coding: utf-8 -*-
from typing import List, Dict, Optional

from socket import socket, AF_INET, SOCK_STREAM
from os import path, chmod, remove
from json import loads
from bcrypt import checkpw, hashpw, gensalt
import mysql.connector

from common.constants import dataTypes
from common.constants import packets
from common.helpers.packetHelper import Packet, Connection
from common.db import dbConnector
from objects import glob

from common.objects.user import User
from common.objects.bottle import Bottle
from common.objects.inventory import BottleCollection

from colorama import init as clr_init, Fore as colour
clr_init(autoreset=True)

with open(f'{path.dirname(path.realpath(__file__))}/config.json', 'r') as f:
    glob.config = loads(f.read())

class Server(object):
    def __init__(self, start_loop: bool = False):
        self.served: int = 0 # Amount of connections served.

        self.users: List[User] = []

        # Attempt connection to MySQL.
        self.db = dbConnector.SQLPool(
            pool_size = 4,
            config = {
                'user': glob.config['mysql_user'],
                'password': glob.config['mysql_passwd'],
                'host': glob.config['mysql_host'],
                'port': 3306,
                'database': glob.config['mysql_database']
            }
        )

        # Create socket (check and remove if prior version exists).
        if path.exists(glob.config['socket_location']):
            remove(glob.config['socket_location'])

        # Actual socket
        self._sock: socket = socket(AF_INET, SOCK_STREAM)
        self._sock.bind(('', glob.config['port']))
        self._sock.listen(glob.config['concurrent_connections'])

        self.sock: Optional[socket] = None # Current 'instance' socket.

        print(f'[SERV] {colour.CYAN}Drink with Friends v{glob.config["version"]:.2f} @ localhost:{glob.config["port"]}')

        if start_loop:
            self.handle_connections()

        return

    def __del__(self) -> None:
        self.db.pool._remove_connections()
        return

    def send_byte(self, packet_id) -> None:
        self.sock.send(packet_id.to_bytes(1, 'little'))
        return

    def handle_connections(self) -> None:
        while True:
            with self._sock.accept()[0] as self.sock: # Don't even take the addr lol
                data: Optional[bytes] = self.sock.recv(glob.max_bytes)
                if len(data) == glob.max_bytes:
                    print('[WARN] Max connection data recived. Most likely missing some data! (ignoring req)\n{data}')
                    return

                conn = Connection(data)
                #try: conn = Connection(data)
                #except:
                #    print('Ignored unknown packet')
                #    del data
                #    return
                #else: del data
                del data

                with Packet() as packet:
                    packet.read_data(conn.body)
                    self._handle_connection(packet)
                del conn
            self.served += 1

    def _handle_connection(self, packet: Packet) -> None:
        if packet.id == packets.client_login: # Login packet
            username, client_password, game_version = packet.unpack_data([ # pylint: disable=unbalanced-tuple-unpacking
                dataTypes.STRING, # Username
                dataTypes.STRING, # Password
                dataTypes.INT16 # Game version
            ])

            del packet

            if game_version < 100:
                print(f'{username} attempted to login with an out-of-date client -- v{game_version}.')
                return

            res = self.db.fetch('SELECT id, password, privileges FROM users WHERE username_safe = %s', [User.safe_username(username)])

            if not res:
                self.send_byte(packets.server_generalNoSuchUsername)
                return

            u = User(res['id'], username, res['privileges'])

            # TODO: bcrypt
            #if not checkpw(client_password.encode(), res['password'].encode()):
            if not client_password == res['password']:
                self.send_byte(packets.server_generalIncorrectPassword)
                return

            del client_password, res

            if not u.privileges:
                print(f'Banned user {username} attempted to login.')
                self.send_byte(packets.server_generalBanned)
                return

            """ Login success, nothing wrong™️ """
            print(f'{username} has logged in.')
            if u.id not in [_u.id for _u in self.users]: self.users.append(u)

            self.send_byte(packets.server_generalSuccess)
            packet = Packet(packets.server_sendUserInfo)

            packet.pack_data([
                [u.id, dataTypes.INT16],
                [u.privileges, dataTypes.INT16],
                [[[_u.username, _u.id, _u.privileges] for _u in self.users], dataTypes.USERINFO_LIST]
            ])

            self.sock.send(packet.get_data())
            del packet

        elif packet.id == packets.client_logout:
            index = [u.id for u in self.users].index(packet.unpack_data([dataTypes.INT16])[0])
            print(f'{self.users[index].username} has logged out.')
            del self.users[index]
            del packet

        elif packet.id == packets.client_getOnlineUsers:
            del packet
            self.sendUserList()
        elif packet.id == packets.client_registerAccount:
            resp: bytes = packet.unpack_data([dataTypes.STRING, dataTypes.STRING])
            if len(resp) == 2: username, password = resp
            else:
                self.send_byte(packets.server_generalFailure)
                return

            if all((len(username) not in range(3, 17), len(password) in range(6, 33))):
                self.send_byte(packets.server_generalFailure)
                return
            del packet

            # Check if username already exists
            if self.db.fetch('SELECT 1 FROM users WHERE username = %s', [username]):
                self.send_byte(packets.server_registrationUsernameTaken)
                return

            """ Passed checks """

            # Add user to DB.
            self.db.execute(
                'INSERT INTO users (id, username, username_safe, privileges, password) VALUES (NULL, %s, %s, 1, %s)',
                [username, User.safe_username(username), password]
            )
            del username, password
            self.send_byte(packets.server_generalSuccess)
        elif packet.id == packets.client_addBottle: # TODO: return failed packet rather than returning during fails
            resp: bytes = packet.unpack_data([
                dataTypes.INT16,  # userid
                dataTypes.DRINK
            ])
            del packet
            if len(resp) != 4:
                del resp
                return

            user_id = resp[0]
            b: Bottle = Bottle(*resp[1:4])
            del resp

            if not b.is_valid():
                del user_id
                self.send_byte(packets.server_generalFailure)
                return

            """ Passed checks """
            self.db.execute(
                'INSERT INTO bottles (id, user_id, name, volume, abv) VALUES (NULL, %s, %s, %s, %s)',
                [user_id, b.name, b.volume, b.abv]
            )

            print(f'{user_id} added bottle: {b.name} [{b.volume}ml @ {b.abv}%]')
            self.send_byte(packets.server_generalSuccess)
            del user_id
        elif packet.id == packets.client_getInventory:
            user_id: int = packet.unpack_data([dataTypes.UINT16])[0] # TODO: get_userid function?
            del packet

            if user_id not in (u.id for u in self.users):
                return # TODO: make not_logged_in packet, generalize these

            res = self.db.fetchall('SELECT name, volume, abv FROM bottles WHERE user_id = %s AND volume > 0', [user_id])
            if not res:
                self.send_byte(packets.server_alreadyUpToDate)
                return

            with Packet(packets.server_sendInventory) as packet:
                packet.pack_data([
                    [[[row['name'], row['volume'], row['abv']] for row in res], dataTypes.DRINK_LIST]
                ])
                self.sock.send(packet.get_data())
        elif packet.id == packets.client_takeShot:
            resp: bytes = packet.unpack_data([ # TODO: only send bottleid
                dataTypes.INT16, # userid
                dataTypes.DRINK  # updated bottle information
            ])
            del packet
            if len(resp) != 4:
                self.send_byte(packets.server_generalFailure)
                del resp
                return

            user_id = resp[0]
            b: Bottle = Bottle(*resp[1:4])
            del resp

            #if not b.is_valid():
            #    del user_id
            #    self.send_byte(packets.server_generalFailure)
            #    return

            # Ensure the drink exists.

            res = self.db.fetch('SELECT id FROM bottles WHERE user_id = %s AND name = %s AND abv = %s', [user_id, b.name, b.abv])
            if not res:
                self.send_byte(packets.server_generalFailure)
                return

            bottle_id: int = res['id']
            del res

            """ Passed checks """

            self.db.execute( # Don't delete from inv so we can use name from bottles in ledger.
                'UPDATE bottles SET volume = %s WHERE user_id = %s AND name = %s AND abv = %s',
                [b.volume, user_id, b.name, b.abv]
            )

            self.db.execute( # Update ledger
                'INSERT INTO ledger (id, user_id, volume, bottle, time) VALUES (NULL, %s, %s, %s, UNIX_TIMESTAMP())',
                [user_id, b.volume, bottle_id]
            )

            #if b.volume:
            #    self.db.execute('UPDATE bottles SET volume = %s WHERE user_id = %s AND name = %s AND abv = %s', [b.volume, user_id, b.name, b.abv])
            #else: # they finished bottle, delete from db
            #    self.db.execute('DELETE FROM bottles WHERE user_id = %s AND name = %s AND abv = %s', [user_id, b.name, b.abv])


            self.send_byte(packets.server_generalSuccess)
        elif packet.id == packets.client_getLedger:
            user_id: int = packet.unpack_data([dataTypes.INT16])[0]
            del packet

            if user_id not in (u.id for u in self.users):
                return # TODO: make not_logged_in packet, generalize these

            res = self.db.fetchall('''
                SELECT bottles.name, ledger.volume, bottles.abv
                FROM ledger
                LEFT JOIN bottles ON bottles.id = ledger.bottle
                WHERE ledger.user_id = %s''', [user_id]
            )

            if not res:
                self.send_byte(packets.server_alreadyUpToDate)
                return

            with Packet(packets.server_sendInventory) as packet:
                packet.pack_data([
                    [[[row['name'], row['volume'], row['abv']] for row in res], dataTypes.DRINK_LIST]
                ])
                self.sock.send(packet.get_data())
        else:
            print(f'Unfinished packet requeted -- ID: {packet.id}')
            self.send_byte(packets.server_generalFailure)
        return

    def sendUserList(self) -> None:
        with Packet(packets.server_sendOnlineUsers) as packet:
            packet.pack_data([
                [[[u.username, u.id, u.privileges] for u in self.users], dataTypes.USERINFO_LIST]
            ])
            self.sock.send(packet.get_data())
        return

if __name__ == '__main__':
    Server(start_loop = True)
