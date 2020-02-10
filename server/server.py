# -*- coding: utf-8 -*-
from typing import List, Dict, Optional

from socket import socket, AF_INET, SOCK_STREAM
from os import path, chmod, remove
from json import loads
import mysql.connector

from common.constants import dataTypes
from common.constants import packetID
from common.helpers.packetHelper import Packet
from common.db import dbConnector
from objects import glob

from colorama import init as clr_init, Fore as colour
clr_init(autoreset=True)

with open(f'{path.dirname(path.realpath(__file__))}/config.json', 'r') as f:
    glob.config = loads(f.read())

""" Attempt to connect to MySQL. """
# glob.db = dbConnector.SQLPool(
#     pool_size = 4,
#     config = {
#         'user': glob.config['mysql_user'],
#         'password': glob.config['mysql_passwd'],
#         'host': glob.config['mysql_host'],
#         'database': glob.config['mysql_database']
#     }
# )

class Connection(object):
    def __init__(self, request_data: bytes) -> None:
        print(f'RAW\n{request_data}\n')
        self.raw_request: List[str] = request_data.decode().split('\r\n\r\n', maxsplit=1) # very unsafe
        self.headers: Dict[str, str] = {}
        self.body: List[str] = []
        self.parse_request()

    def parse_request(self) -> None:
        self.parse_headers()
        self.body = self.raw_request[1]#.split('\n')

    def parse_headers(self) -> None:
        for line in self.raw_request[0].split('\r\n'):
            if ':' not in line: continue
            k, v = line.split(':')
            self.headers[k] = v.lstrip()

# Create socket (check and remove if prior version exists).
if path.exists(glob.config['socket_location']):
    remove(glob.config['socket_location'])

sock: socket = socket(AF_INET, SOCK_STREAM)
sock.bind(('', 6999))
sock.listen(glob.config['concurrent_connections'])

def handle_connection(conn: socket) -> None:
    data: Optional[bytes] = conn.recv(128) # may need to be increased in the future?
    if len(data) == 128:
        print('[WARN] Max connection data recived. Most likely missing some data! (ignoring req)\n{data}')
        return

    c = Connection(data)
    p = Packet()
    p.read_data(c.body)

    if p.id == 1: # Login packet
        print(p.unpack_data((dataTypes.STRING,)))
    return

if __name__ == '__main__':
    print(f'[SERV] {colour.CYAN}Drink with Friends v{glob.config["version"]:.2f}')

    while True:
        conn, _ = sock.accept()
        with conn: handle_connection(conn)

# Free SQL connections
glob.db.pool._remove_connections()
