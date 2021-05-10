import os
import sys
import argparse
import socket
import json
from collections import namedtuple

import pymysql
import django

from DataManagement.models import *


Coord = namedtuple('Coord', 'latitude', 'longitude')

STATIONINFO = {
    ...
}


os.environ['DJANGO_SETTINGS_MODULE'] = 'WebMysql.settings'
django.setup()


def parse_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('--addr', type=str, default='127.0.0.1')
    parser.add_argument('--port', type=int)
    parser.add_argument('--debug', type=bool, default=True)
    return parser.parse_args()


def convert_slice(path: str):
    """Converts binary number from SLICE file to decimal number."""
    with open(path, 'rb') as f:
        data = f.read()[24:]
        while data:
            # TODO bin to dec
            data = data[2:]
    return


class RpcClient(object):

    def __init__(self, addr, port):

        self.db = pymysql.connect(
            host='localhost', port=3306, db='thunder',
            user='root', passwd='xuyifei')
        self.cursor = self.db.cursor()
        self.cursor.execute("SELECT * FROM waveinfo_rs")
        if DEBUG:
            print('[DB] Database connected.')

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((addr, port))
        if DEBUG:
            print('[RPC] Socket connected.')

    def exit(self):
        self.sock.sendall('-2'.zfill(5).encode())
        self.sock.close()
        self.cursor.close()
        self.db.close()
        sys.exit()

    def loop(self) -> None:

        def fetch_data(cursor) -> tuple[str, dict]:
            """Fetch data from database."""
            def extract_data(data: tuple) -> dict:
                """Extract a dict of input data from data fetched from database."""
                DATETIME = 1
                MICROSEC = 2    # Actually 0.1 ms.
                STATIONNAME = 3
                PEAKVALUE = 7
                return {
                    'datetime': data[DATETIME].strftime('%Y-%m-%d %H:%M:%S'),
                    'microsecond': data[MICROSEC],
                    'node': data[STATIONNAME],
                    'latitude': STATIONINFO[data[STATIONNAME]].latitude,
                    'longitude': STATIONINFO[data[STATIONNAME]].longitude,
                    'signal_strength': data[PEAKVALUE],
                }

            data = cursor.fetchone()
            if data is not None:
                data_dict = extract_data(data)
                return data_dict['datetime'], data_dict
            else:
                self.exit()

        def ltgpos_rpc(sock, data: list[dict]) -> None:
            """
            Header:
                5 bytes.
                >0: length of data string.
                -1: Close socket.
                -2: Close server.
            """
            data_json = json.dumps(data)
            data = str(len(data_json)).zfill(5) + data_json
            sock.sendall(data.encode())
            res = sock.recv(8192 * 8)
            # TODO write to database
            print(res)

        prev_datetime, data = fetch_data(self.cursor)
        data_batch = [data]

        while True:
            datetime, data = fetch_data(self.cursor)
            if datetime == prev_datetime:
                data_batch.append(data)
            else:
                ltgpos_rpc(self.sock, data_batch)
                datetime, data = fetch_data(self.cursor)
            prev_datetime = datetime


if __name__ == '__main__':
    args = parse_args()
    global DEBUG
    DEBUG = args.debug

    server = RpcClient(args.addr, args.port)
    ...
