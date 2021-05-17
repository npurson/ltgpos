import sys
import argparse
import socket
import json
import warnings
from typing import Tuple, List

import pymysql
from utils import StationInfo, convert_slice


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--addr', type=str, default='127.0.0.1')
    parser.add_argument('--port', type=int)
    parser.add_argument('--debug', type=bool, default=True)
    return parser.parse_args()


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

        def fetch_data(cursor) -> Tuple[str, dict]:
            """Fetch data from database."""

            def extract_data(data: tuple) -> dict:
                """Extract a dict of input data from data fetched from database."""
                GUID = 0
                DATETIME = 6
                STATIONNAME = 3
                PEAKVALUE = 7
                return {
                    'guid': data[GUID],
                    'datetime': data[DATETIME].split('_')[0],
                    'microsecond': int(data[DATETIME].split('_')[1]),
                    'node': data[STATIONNAME],
                    'latitude': StationInfo[data[STATIONNAME]].latitude,
                    'longitude': StationInfo[data[STATIONNAME]].longitude,
                    'signal_strength': data[PEAKVALUE] }

            while True:
                data = cursor.fetchone()
                if data is None:            # Database cleared.
                    self.exit()
                elif data[3] not in StationInfo:
                    warnings.warn('unregistered station name.', UserWarning)
                else:
                    break
            data_dict = extract_data(data)
            return data_dict['datetime'], data_dict

        def ltgpos_rpc(sock, data: List[dict]) -> None:
            """
            Header:
                5 bytes.
                >0: length of data string.
                -1: Close socket.
                -2: Close server.
            """
            # TODO Deduplicate and sort
            if len(data) < 3:
                return

            data_json = json.dumps(data)
            data = str(len(data_json)).zfill(5) + data_json
            print(data)
            sock.sendall(data.encode())
            res = sock.recv(8192 * 8)
            # TODO write to database
            print(res)
            return

        data_batch = None
        while True:
            if data_batch is None:
                prev_datetime, data = fetch_data(self.cursor)
                data_batch = [data]
                continue

            datetime, data = fetch_data(self.cursor)
            if datetime == prev_datetime:
                data_batch.append(data)
            else:
                ltgpos_rpc(self.sock, data_batch)
                data_batch = None


if __name__ == '__main__':
    args = parse_args()
    global DEBUG
    DEBUG = args.debug

    server = RpcClient(args.addr, args.port)
    server.loop()
