import os
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
CURSOR_SAVE = 'cursor.txt'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--addr', type=str)
    parser.add_argument('--port', type=int)
    parser.add_argument('--debug', type=bool, default=True)
    parser.add_argument('--start', type=str, default='')
    parser.add_argument('--end', type=str, default='')
    parser.add_argument('--database', type=str, default='')
    return parser.parse_args()


class RpcClient(object):

    def __init__(self, args):

        self.args = args
        self.db = pymysql.connect(
            host='localhost', port=3306, db='thunder',
            user='root', passwd='xuyifei')
            # host='localhost', db='thunder',
            # user='root', passwd='123456')

        self.src_cursor = self.db.cursor()
        self.start_datetime, self.end_datetime, self.tar_database = None, None, 'ltgpos_rs'


        if os.path.isfile(CURSOR_SAVE):
            with open(CURSOR_SAVE, 'r') as f:
                lines = f.readlines()
                start_lines = None if len(lines) == 0 else lines[0].strip('\n').split('=')
                database_lines = None if len(lines) <= 1 else lines[1].strip('\n').split('=')
                start_date = None if 'datetime' not in start_lines else start_lines[-1]
                database = None if 'database' not in database_lines else database_lines[-1]
                self.start_datetime = start_date
                self.tar_database = database
        #     self.src_cursor.execute('SELECT * FROM waveinfo_rs where trigertime > "' + self.start_datetime + '" order by trigertime')
        # else:
        #     self.src_cursor.execute('SELECT * FROM waveinfo_rs order by trigertime')

        self.run_sql()
        self.tar_cursor = self.db.cursor()
        self.tar_cursor.execute('select TABLE_NAME, table_type, engine from information_schema.tables where table_schema="thunder"')

        tables = [i[0] for i in self.tar_cursor._rows]
        if self.tar_database not in tables:
            self.tar_cursor.execute(
                'create table ltgpos_rs ('
                'date_time datetime,'
                'time DECIMAL(10,6),'
                'latitude DECIMAL(10, 6),'
                'longitude DECIMAL(10, 6),'
                'altitude DECIMAL(10, 6),'
                'goodness DECIMAL(10, 6),'
                'current DECIMAL(10, 6))')

        # TODO verify keys.
        self.tar_cursor.execute('DESC ltgpos_rs')
        self.tar_keys = [i[0] for i in self.tar_cursor._rows]

        if DEBUG:
            print('[DB] Database connected.')

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.args.addr, self.args.port))
        if DEBUG:
            print('[RPC] Socket connected.')

    def run_sql(self):
        # If args is not None, update the parameters
        self.start_datetime = args.start if args.start else self.start_datetime
        self.end_datetime = args.end if args.end else self.end_datetime
        self.tar_database = args.database if args.database else self.tar_database
        # Run sql in different modes.
        # import pdb; pdb.set_trace()
        if self.start_datetime and self.end_datetime:
            self.src_cursor.execute(
                'SELECT * FROM waveinfo_rs where trigertime > "' + self.start_datetime +'" trigertime > "' +
                self.end_datetime + '" order by trigertime')
        elif self.start_datetime and not self.end_datetime:
            self.src_cursor.execute(
                'SELECT * FROM waveinfo_rs where trigertime > "' + self.start_datetime + '" order by trigertime')
        else:
            self.src_cursor.execute('SELECT * FROM waveinfo_rs')



    def exit(self):
        self.sock.sendall('-1'.zfill(HEADERLEN).encode())
        self.sock.close()
        self.src_cursor.close()
        self.tar_cursor.close()
        self.db.close()
        with open(CURSOR_SAVE, 'w') as f:
            f.write('datetime=' + self.start_datetime + '\n')
            f.write('database=' + self.tar_database)
        sys.exit()


    def fetch_data(self, cursor) -> Tuple[str, dict]:
        """Fetch data from database."""

        def extract_data(data: tuple) -> dict:
            """Extract a dict of input data from data fetched from database."""
            GUID = 0
            DATETIME = 6
            STATIONNAME = 3
            PEAKVALUE = 7
            ret = {
                'guid': data[GUID],
                'datetime': ' '.join(data[DATETIME].split('_')[:-1]),
                'microsecond': int(data[DATETIME].split('_')[-1]),
                'node': data[STATIONNAME],
                'latitude': StationInfo[data[STATIONNAME]].latitude,
                'longitude': StationInfo[data[STATIONNAME]].longitude,
                'signal_strength': int(data[PEAKVALUE]) }
            self.cur_id = str(data[GUID])
            self.start_datetime = ret['datetime']
            return ret

        while True:
            data = cursor.fetchone()
            if data is None:            # Database cleared.
                self.exit()
            if data[3] not in StationInfo:
                warnings.warn('unregistered station name: ' + data[3], UserWarning)
            else:
                break
        data_dict = extract_data(data)
        return data_dict['datetime'], data_dict

    def ltgpos_rpc(self, data: List[dict]) -> None:
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
        self.sock.sendall(packet.encode())
        output = self.sock.recv(1024 * 8)
        if output == b'ERR':
            print("Error occurred.")
            return
        output = json.loads(output)

        key, value = map(
            lambda l: reduce(
                lambda a, b: str(a) + str(b) + ',', ['('] + list(l)
            )[:-1] + ')', [output.keys(), output.values()])
        value = value.replace('(', '("').replace(',', '",', 1)

        try:
            self.tar_cursor.execute('insert into ltgpos_rs ' + key + ' values ' + value + ';')
            self.db.commit()
        except:
            self.db.rollback()
        return

    def loop(self) -> None:

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
                prev_datetime, data = self.fetch_data(self.src_cursor)
                data_batch = [data]
                continue

            datetime, data = self.fetch_data(self.src_cursor)
            if datetime == prev_datetime:
                data_batch.append(data)
            else:
                data_batches = comb_batch(data_batch)
                for batch in data_batches:
                    self.ltgpos_rpc(batch)
                data_batch = None


if __name__ == '__main__':
    args = parse_args()
    global DEBUG
    DEBUG = args.debug

    server = RpcClient(args)
    server.loop()
