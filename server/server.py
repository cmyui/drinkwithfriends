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

from colorama import init as clr_init, Fore as colour
clr_init(autoreset=True)

with open(f'{path.dirname(path.realpath(__file__))}/config.json', 'r') as f:
    glob.config = loads(f.read())

""" Attempt to connect to MySQL. """
glob.db = dbConnector.SQLPool(
    pool_size = 4,
    config = {
        'user': glob.config['mysql_user'],
        'password': glob.config['mysql_passwd'],
        'host': glob.config['mysql_host'],
        'port': 3306,
        'database': glob.config['mysql_database']
    }
)

class Server(object):
    def __init__(self, start_loop: bool = False):
        self.served: int = 0 # Amount of connections served.

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

                try: conn = Connection(data)
                except:
                    print('Ignored unknown packet')
                    del data
                    return
                else: del data

                with Packet() as packet:
                    packet.read_data(conn.body)
                    self._handle_connection(packet)

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

            res = glob.db.fetch('SELECT id, password, privileges FROM users WHERE username_safe = %s', [username.replace(' ', '_').strip()])

            if not res:
                self.send_byte(packets.server_loginNoSuchUsername)
                return

            u = User(res['id'], username, res['privileges'])

            # TODO: fix password check
            # if not checkpw(client_password.encode(), res['password'].encode()):
            #     self.send_byte(packets.server_loginIncorrectPassword)
            #     self.sock.send(bytes([packets.server_loginIncorrectPassword]))
            #     return

            del client_password, res

            if not u.privileges:
                print(f'Banned user {username} attempted to login.')
                self.send_byte(packets.server_loginBanned)
                return

            """ Login success, nothing wrong™️ """
            print(f'{username} has logged in.')

            glob.users.append(u)
            self.send_byte(packets.server_loginSuccess)
            packet = Packet(packets.server_sendUserInfo)

            packet.pack_data([
                (u.id, dataTypes.INT16), # the user's userid, from db
                ([u.id for u in glob.users], dataTypes.INT16_LIST) # length will be added as a single byte at beginning
            ])

            self.sock.send(packet.get_data())
            del packet

        elif packet.id == packets.client_logout:
            index = [u.id for u in glob.users].index(packet.unpack_data([dataTypes.INT16])[0])
            print(f'{glob.users[index].username} has logged out.')
            del glob.users[index]

        elif packet.id == packets.client_getOnlineUsers:
            packet.pack_data([
                ([u.id for u in glob.users], dataTypes.INT16_LIST),
            ])
            self.sock.send(packet.get_data())
            del packet
        else:
            print(f'Unfinished packet requeted -- ID: {packet.id}')

        return

if __name__ == '__main__':
    Server(start_loop = True)

    # Free SQL connections
    glob.db.pool._remove_connections()
