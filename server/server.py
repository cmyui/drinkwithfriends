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
            self._handle_connections()

        return

    def sendPacketID(self, packet_id) -> None:
        self.sock.send(packet_id.to_bytes(1, 'little'))
        return

    def _handle_connections(self) -> None:
        while True:
            self.sock, _ = self._sock.accept()
            with self.sock: self.handle_connection()
            self.served += 1

    def handle_connection(self) -> None:
        data: Optional[bytes] = self.sock.recv(128) # may need to be increased in the future?
        print(data)
        if len(data) == 128:
            print('[WARN] Max connection data recived. Most likely missing some data! (ignoring req)\n{data}')
            return

        try: conn = Connection(data)
        except:
            print('Ignored unknown packet')
            return

        p = Packet()
        p.read_data(conn.body)

        if p.id == packets.client_login: # Login packet
            username, client_password, game_version = p.unpack_data([ # pylint: disable=unbalanced-tuple-unpacking
                dataTypes.STRING, # Username
                dataTypes.STRING, # Password
                dataTypes.INT16 # Game version
            ])
            #except Exception as err:
            #    print(err)
            #    self.sendPacketID(packets.server_loginInvalidData)
            #    #self.sock.send(bytes([packets.server_loginInvalidData]))
            #    return

            # TODO: future 'anticheat' checks with game_version

            res = glob.db.fetch('SELECT id, password, privileges FROM users WHERE username_safe = %s', [username.replace(' ', '_').strip()])

            if not res:
                self.sendPacketID(packets.server_loginNoSuchUsername)
                #self.sock.send(bytes([packets.server_loginNoSuchUsername]))
                return

            u = User(res['id'], username, res['privileges'], game_version)
            # TODO: fix password check
            # if not checkpw(client_password.encode(), res['password'].encode()):
            #     self.sendPacketID(packets.server_loginIncorrectPassword)
            #     self.sock.send(bytes([packets.server_loginIncorrectPassword]))
            #     return

            del client_password, res

            if not u.privileges:
                print(f'Banned user {username} attempted to login.')
                self.sendPacketID(packets.server_loginBanned)
                #self.sock.send(bytes([packets.server_loginBanned]))
                return

            """ Login success, nothing wrong™️ """
            print(f'{username} has logged in.')

            glob.users.append(u)
            self.sendPacketID(packets.server_loginSuccess)
            #self.sock.send(bytes([packets.server_loginSuccess])) # send success
            p = Packet(packets.server_userInfo)

            p.pack_data([
                (u.id, dataTypes.INT16), # the user's userid, from db
                #(glob.users.__len__(), dataTypes.INT16), # the length of
                ([u.id for u in glob.users], dataTypes.INT16_LIST)
            ])

            #p.pack_data((
            #    (u.id, dataTypes.UINT16),
            #    (len(glob.users), dataTypes.UINT16), # Length of the list of online users
            #    (([u.id for u in glob.users]), dataTypes.INT16_LIST)
            #    #*((u.id, dataTypes.UINT16) for u in glob.users) # List of online users
            #))

            self.sock.send(p.get_data())
            return

        elif p.id == packets.client_addBottle: # Adding a bottle to a user's inventory.
            pass
        elif p.id == packets.client_takeShot: # Taking a shot.
            pass

        return

if __name__ == '__main__':
    Server(start_loop = True)

    # Free SQL connections
    glob.db.pool._remove_connections()
