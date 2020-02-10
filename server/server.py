# -*- coding: utf-8 -*-
from typing import List, Dict, Optional

from socket import socket, AF_INET, SOCK_STREAM
from os import path, chmod, remove
from json import loads
from bcrypt import checkpw, hashpw, gensalt
import mysql.connector

from common.constants import dataTypes
from common.constants import packetID
from common.helpers.packetHelper import Packet
from common.db import dbConnector
from objects import glob
from objects.user import User

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
        'database': glob.config['mysql_database']
    }
)

class Connection(object):
    def __init__(self, data: bytes) -> None:
        self.raw: List[str] = data.split(b'\r\n\r\n', maxsplit = 1)
        self.headers: List[str] = []
        self.parse_headers(self.raw[0].split(b'\r\n'))
        self.body: str = self.raw[1]

        return

    def parse_headers(self, _headers: bytes) -> None:
        for line in self.raw[0].split('\r\n'):
            if ':' not in line: continue
            k, v = line.split(':')
            self.headers[k] = v.lstrip()
        return

class Server(object):
    def __init__(self, start_loop: bool = False):
        self.served: int = 0 # Amount of connections served.

        # Create socket (check and remove if prior version exists).
        if path.exists(glob.config['socket_location']):
            remove(glob.config['socket_location'])

        self.sock: socket = socket(AF_INET, SOCK_STREAM)
        self.sock.bind(('', glob.config['port']))
        self.sock.listen(glob.config['concurrent_connections'])

        if start_loop:
            self._handle_connections()

        pass

    def _handle_connections(self) -> None:
        while True:
            self.sock, _ = self.sock.accept()
            with self.sock: self.handle_connection()
            self.served += 1

    def handle_connection(self) -> None:
        data: Optional[bytes] = self.sock.recv(128) # may need to be increased in the future?
        if len(data) == 128:
            print('[WARN] Max connection data recived. Most likely missing some data! (ignoring req)\n{data}')
            return

        conn = Connection(data)
        p = Packet()
        p.read_data(conn.body)

        if p.id == packetID.client_login: # Login packet
            try:
                username, client_password, game_version = p.unpack_data(( # pylint: disable=unbalanced-tuple-unpacking
                    dataTypes.STRING, # Username
                    dataTypes.STRING, # Password
                    dataTypes.UINT # Game version
                ))
            except:
                self.sock.send(bytes([packetID.server_loginInvalidData]))
                return

            # TODO: future 'anticheat' checks with game_version

            u = User(username, game_version)

            res = glob.db.fetch('SELECT id, password, privileges FROM users WHERE username_safe = %s', [u.username_safe])
            if not res:
                self.sock.send(bytes([packetID.server_loginNoSuchUsername]))
                return

            print(checkpw(client_password.encode(), res['password'].encode()))
            if not checkpw(client_password.encode(), res['password'].encode()):
                self.sock.send(bytes([packetID.server_loginIncorrectPassword]))
                return

            if not res['privileges']:
                self.sock.send(bytes([packetID.server_loginBanned]))
                return

            """ Login success, nothing wrong™️ """

            glob.users.append(u)
            self.sock.send(bytes([packetID.server_loginSuccess])) # send success
            return

        elif p.id == packetID.client_shot: # Taking a shot
            pass

        return

def handle_connection(conn: socket) -> None:
    data: Optional[bytes] = conn.recv(128) # may need to be increased in the future?
    if len(data) == 128:
        print('[WARN] Max connection data recived. Most likely missing some data! (ignoring req)\n{data}')
        return

    c = Connection(data)
    p = Packet()
    p.read_data(c.body)

    if p.id == packetID.client_login: # Login packet
        try:
            username, client_password, game_version = p.unpack_data(( # pylint: disable=unbalanced-tuple-unpacking
                dataTypes.STRING, # Username
                dataTypes.STRING, # Password
                dataTypes.UINT # Game version
            ))
        except:
            conn.send(bytes([packetID.server_loginInvalidData]))
            return

        # TODO: future 'anticheat' checks with game_version
        u = User(username, game_version)

        res = glob.db.fetch('SELECT id, password, privileges FROM users WHERE username_safe = %s', [u.username_safe])
        if not res:
            conn.send(bytes([packetID.server_loginNoSuchUsername]))
            return

        print(checkpw(client_password.encode(), res['password'].encode()))
        if not checkpw(client_password.encode(), res['password'].encode()):
            conn.send(bytes([packetID.server_loginIncorrectPassword]))
            return

        if not res['privileges']:
            conn.send(bytes([packetID.server_loginBanned]))
            return

        """ Login success, nothing wrong™️ """

        glob.users.append(u)
        conn.send(bytes([packetID.server_loginSuccess])) # send success
        return

    elif p.id == packetID.client_shot: # Taking a shot
        pass

    return

if __name__ == '__main__':
    print(f'[SERV] {colour.CYAN}Drink with Friends v{glob.config["version"]:.2f}')

    Server(True)

    #while True:
    #    conn, _ = sock.accept()
    #    with conn: handle_connection(conn)
    #    glob.served += 1

# Free SQL connections
glob.db.pool._remove_connections()
