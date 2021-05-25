import sys
import argparse
import json
import warnings
from typing import Tuple, List

from utils import StationInfo, convert_slice


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', type=str)
    return parser.parse_args()


class FakeClient(object):

    def __init__(self, file):
        self.cursor = open(file)

    def exit(self):
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
                data = cursor.readline().strip()
                if data is None:            # Database cleared.
                    self.exit()
                data = [d for d in data.split(',')]
                if data[3] not in StationInfo:
                    warnings.warn('unregistered station name.', UserWarning)
                else:
                    break
            data_dict = extract_data(data)
            return data_dict['datetime'], data_dict

        def ltgpos_rpc(sock, data: List[dict]) -> None:
            """
            Header:
                4 bytes.
                >0: length of data string.
                -1: Close socket.
                -2: Close server.
            """
            data_json = json.dumps(data)
            # data = str(len(data_json)).zfill(5) + data_json
            data = data_json
            print(data)
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

            # for b in data_batches:
            #     # dt = [b[i+1]['microsecond'] - b[i]['microsecond'] for i in range(len(b) - 1)]
            #     # print(dt)
            #     # import numpy as np
            #     # if sum(np.array(dt) > 700):
            #     #     import pdb; pdb.set_trace()
            #     print('### Begin of A Batch ###')
            #     for d in b:
            #         print(d)
            #     print('#### End of A Batch ####')
            # print()
            return data_batches

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
                data_batches = comb_batch(data_batch)
                for batch in data_batches:
                    ltgpos_rpc(None, batch)
                data_batch = None


if __name__ == '__main__':
    args = parse_args()
    server = FakeClient(args.file)
    server.loop()
