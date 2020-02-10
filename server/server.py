# -*- coding: utf-8 -*-
from typing import (
    Optional
)

from socket import socket, AF_UNIX, SOCK_STREAM
from os import path, chmod, remove
from json import loads
import mysql.connector

from db import dbConnector
from objects import glob

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

# just don't error lol 4head
#except SQLError as err:
#    if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
#        raise Exception('Something is wrong with your username or password.')
#    elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
#        raise Exception('Database does not exist.')
#    else: raise Exception(err)
#else: print(f'{colour.GREEN}Successfully connected to SQL.')

# Create socket (check and remove if prior version exists).
if path.exists(glob.config['socket_location']):
    remove(glob.config['socket_location'])

sock: socket = socket(AF_UNIX, SOCK_STREAM)
sock.bind(glob.config['socket_location'])
chmod(glob.config['socket_location'], 0o777)
sock.listen(glob.config['concurrent_connections'])

def handle_connection(conn: socket) -> None:
    data: Optional[bytes] = conn.recv(2048)
    print(data)
    return

if __name__ == '__main__':
    print(f'[SERV] {colour.CYAN}Drink with Friends v{glob.config["version"]:.2f}')

    while True:
        conn, _ = sock.accept()
        with conn: handle_connection(conn)
