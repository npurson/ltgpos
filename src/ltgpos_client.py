import os
import sys
import argparse
import json
import warnings
from functools import reduce
from typing import Tuple, List
import pymysql

import nrpc
from utils import StationInfo, convert_slice


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--addr', type=str, required=True, help='TODO')
    parser.add_argument('--port', type=int, required=True, help='TODO')
    parser.add_argument('-t', '--start_datetime', type=str, help='TODO')
    parser.add_argument('-e', '--end_datetime', type=str, help='TODO')
    parser.add_argument('-s', '--src_table', type=str,
                        choices=(None, 'waveinfo_rs', 'waveinfo_ic', 'waveinfo_nb', 'waveinfo_pb'),
                        help='TODO')
    parser.add_argument('-d', '--dst_table', type=str, help='TODO')
    parser.add_argument('--alarm', type=bool, default=False, help='TODO')
    return parser.parse_args()


class LtgposClient(object):

    def __init__(self, args):

        self.TIMESTAMP_SAVE = 'timestamp.json'
        if args.alarm and os.path.isfile(self.TIMESTAMP_SAVE):
            with open(self.TIMESTAMP_SAVE) as f:
                timestamps = json.load(f)
                args.start_datetime = timestamps.get(args.src_table)

        self.db = pymysql.connect(
            host='localhost', db='thunder',
            user='root', passwd='123456',
            # host='localhost', db='thunder',
            # user='root', passwd='123456'
        )
        self.src_cursor = self.db.cursor()
        self.tar_cursor = self.db.cursor()

        def sql_select(args) -> str:
            cmd = 'SELECT * FROM ' + args.src_table
            if args.start_datetime or args.end_datetime:
                condition1 = ('trigertime > "' + args.start_datetime + '"'
                              if args.start_datetime else '')
                condition2 = ('trigertime < "' + args.end_datetime + '"'
                              if args.end_datetime else '')
                cmd += ' WHERE ' + (' and ' if args.start_datetime and args.end_datetime
                                    else '').join((condition1, condition2))
            cmd += ' order by trigertime'
            return cmd
        self.src_cursor.execute(sql_select(args))
        self.tar_cursor.execute('SELECT table_name, table_type, engine '
                                'FROM information_schema.tables '
                                'WHERE table_schema="thunder"')

        if not args.dst_table:
            args.dst_table = 'ltgpos_' + '2d' if args.src_table.split('_')[-1] == 'rs' else '2d'  # TODO 3d
        tables = [i[0] for i in self.tar_cursor._rows]
        if args.dst_table not in tables:
            self.tar_cursor.execute(
                'CREATE TABLE ' + args.dst_table + ' ('
                '时间 DATETIME,'
                '微秒 DECIMAL(10, 6),'
                '纬度 DECIMAL(10, 4),'
                '经度 DECIMAL(10, 4),'
                '拟合优度 DECIMAL(10, 6),'
                '电流 DECIMAL(10, 6),'
                '参与站数 int,'
                '参与站 varchar(256),'
                '波形识别号 varchar(256),'
                'IS3D tinyint'
                ')'
            )
        self.tar_cursor.execute('DESC ' + args.dst_table)
        print('Database connected')
        self.rpc_client = nrpc.Client(args.addr, args.port, mode='json', bufsz=5120)
        print('NRPC Client connected')
        self.args = args

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
                'signal_strength': int(data[PEAKVALUE])
            }
            self.cur_datetime = ret['datetime']
            return ret

        while True:
            data = cursor.fetchone()
            if data is None:
                self.exit()
            if data[3] not in StationInfo:
                warnings.warn('unregistered station name: ' + data[3], UserWarning)
            else:
                break
        data_dict = extract_data(data)
        return data_dict['datetime'], data_dict

    def exit(self):
        if args.alarm:
            if os.path.isfile(self.TIMESTAMP_SAVE):
                with open(self.TIMESTAMP_SAVE) as f:
                    timestamps = json.load(f)
            else:
                timestamps = { tb: '' for tb in ('waveinfo_rs', 'waveinfo_ic', 'waveinfo_nb', 'waveinfo_pb') }
            timestamps[args.src_table] = self.cur_datetime
            with open(self.TIMESTAMP_SAVE, 'w') as f:
                json.dump(timestamps, f, indent=4)
            print('Timestamps dumped to ' + self.TIMESTAMP_SAVE)
        self.rpc_client.close_connect()
        self.src_cursor.close()
        self.tar_cursor.close()
        self.db.close()
        sys.exit()

    def ltgpos_rpc(self, data: List[dict]) -> None:
        self.rpc_client.send(data)
        output = self.rpc_client.recv()
        output['n_involved'] = len(output['involvedNodes'])
        if not output:
            print('Exception occurred')
            return  # exception
        output['involvedNodes'] = ' '.join(output['involvedNodes'])
        output['is3d'] = 0 if self.args.src_table == 'waveinfo_rs' else 1

        key_map = { 'date_time': '时间', 'time': '微秒', 'latitude': '纬度', 'longitude': '经度', 'altitude': '高度',
                    'goodness': '优度', 'current': '电流', 'n_involved': '参与站数', 'involvedNodes': '参与站',
                    'wave_id': '波形识别号', 'is3d': 'IS3D' }
        key = str(tuple([key_map[k] for k in output.keys()])).replace("'", "")
        value = str(tuple([v for v in output.values()]))
        sql_insert = 'INSERT INTO ' + self.args.dst_table + ' ' + key + ' values ' + value + ';'

        try:
            self.tar_cursor.execute(sql_insert)
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
    assert args.addr and args.port
    if args.alarm:
        assert args.start_datetime is None and args.end_datetime is None and args.src_table is None and args.dst_table is None, \
            'Received not-none arguments when auto pulled up.'
        for t in ('waveinfo_rs', 'waveinfo_ic', 'waveinfo_nb', 'waveinfo_pb'):
            args.src_table = t
            client = LtgposClient(args)
            client.loop()

    else:
        assert args.src_table, 'Received no argument for src_table when manual pulled up.'
        client = LtgposClient(args)
        client.loop()
