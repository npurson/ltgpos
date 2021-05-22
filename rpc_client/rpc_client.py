import sys
import argparse
import socket
import json
import warnings
from functools import reduce
from typing import Tuple, List

import pymysql
from utils import StationInfo, convert_slice


HEADERLEN = 4
BUFSIZE = 8192


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
        self.src_cursor = self.db.cursor()
        self.src_cursor.execute("SELECT * FROM waveinfo_rs")

        self.tar_cursor = self.db.cursor()
        self.tar_cursor.execute('select TABLE_NAME, table_type, engine from information_schema.tables where table_schema="thunder"')
        tables = [i[0] for i in self.tar_cursor._rows]
        if 'result' not in tables:
            self.tar_cursor.execute(
                'create table result ('
                'date_time DATETIME,'
                'time DECIMAL(10,6),'
                'latitude DECIMAL(10, 6),'
                'longitude DECIMAL(10, 6),'
                'altitude DECIMAL(10, 6),'
                'goodness DECIMAL(10, 6),'
                'current DECIMAL(10, 6))')

        # TODO verify keys.
        self.tar_cursor.execute('DESC result')
        self.tar_keys = [i[0] for i in self.tar_cursor._rows]

        if DEBUG:
            print('[DB] Database connected.')

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((addr, port))
        if DEBUG:
            print('[RPC] Socket connected.')

    def exit(self):
        self.sock.sendall('-2'.zfill(HEADERLEN).encode())
        self.sock.close()
        self.src_cursor.close()
        self.tar_cursor.close()
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
                    'datetime': ' '.join(data[DATETIME].split('_')[:-1]),
                    'microsecond': int(data[DATETIME].split('_')[-1]),
                    'node': data[STATIONNAME],
                    'latitude': StationInfo[data[STATIONNAME]].latitude,
                    'longitude': StationInfo[data[STATIONNAME]].longitude,
                    'signal_strength': int(data[PEAKVALUE]) }

            while True:
                data = cursor.fetchone()
                if data is None:            # Database cleared.
                    self.exit()
                if data[3] not in StationInfo:
                    warnings.warn('unregistered station name.', UserWarning)
                else:
                    break
            data_dict = extract_data(data)
            return data_dict['datetime'], data_dict

        def ltgpos_rpc(sock, data: List[dict]) -> None:
            """
            Header:
                4(HEADERLEN) bytes.
                >0: length of data string.
                -1: Close socket.
                -2: Close server.
            """
            data_json = json.dumps(data)
            # Cuts off JSON string if its length larger than buffer size.
            if len(data_json) > BUFSIZE - HEADERLEN:
                data_json = data_json[:BUFSIZE - HEADERLEN]
                data_json = data_json[:data_json.rfind('}') + 2]
                data_json[-1] = ']'

            packet = str(len(data_json)).zfill(HEADERLEN) + data_json
            sock.sendall(packet.encode())

            output = sock.recv(1024 * 8)
            output = json.loads(output)
            key, value = map(
                lambda l: reduce(lambda a, b: a + b + ',', ['('] + l)[:-1] + ')',
                [output.keys(), output.values()])

            try:
                self.tar_cursor.execute('insert into result ' + key + ' values ' + value)
                self.db.commit()
            except:
                self.db.rollback()
            return

        def comb_batch(data_batch: List[dict]) -> List[List[dict]]:
            """Split a batch of data into several batches for computing."""
            data_batch = sorted(data_batch, key=lambda d:d['microsecond'])
            data_batches = []
            for i, data in enumerate(data_batch):
                if i != 0 and data['microsecond'] - prev_ms < 3000:             # dtime threshold: 300us, most < 60 us
                    if (data['microsecond'] - prev_data['microsecond'] < 5 and  # Deduplicates data batch.
                        data['node'] == prev_data['node'] and
                        data['signal_strength'] == prev_data['signal_strength']):
                        continue
                    batch.append(data)
                else:
                    if i != 0 and len(batch) >= 3:
                        data_batches.append(batch)
                    batch = [data]
                prev_ms = data['microsecond']
                prev_data = data
            return data_batches

        data_batch = None
        while True:
            if data_batch is None:
                prev_datetime, data = fetch_data(self.src_cursor)
                data_batch = [data]
                continue

            datetime, data = fetch_data(self.src_cursor)
            if datetime == prev_datetime:
                data_batch.append(data)
            else:
                data_batches = comb_batch(data_batch)
                for batch in data_batches:
                    ltgpos_rpc(self.sock, batch)
                data_batch = None


if __name__ == '__main__':
    args = parse_args()
    global DEBUG
    DEBUG = args.debug

    server = RpcClient(args.addr, args.port)
    server.loop()
