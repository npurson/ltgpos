import sys
import argparse
import json
import warnings
from typing import Tuple, List

from utils import StationInfo


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', type=str)
    return parser.parse_args()


class RpcClient(object):

    def __init__(self, f):
        self.cursor = f

    def exit(self):
        sys.exit()

    def loop(self) -> None:

        def fetch_data(cursor) -> Tuple[str, dict]:
            """Fetch data from database."""

            def extract_data(data: tuple) -> dict:
                """Extract a dict of input data from data fetched from database."""
                DATETIME = 1
                MICROSEC = 2    # Actually 0.1 ms.
                STATIONNAME = 3
                PEAKVALUE = 7
                return {
                    'datetime': data[DATETIME],
                    'microsecond': int(data[MICROSEC]),
                    'node': data[STATIONNAME],
                    'latitude': StationInfo[data[STATIONNAME]].latitude,
                    'longitude': StationInfo[data[STATIONNAME]].longitude,
                    'signal_strength': float(data[PEAKVALUE]), }
            
            def split(input: str) -> tuple:
                return tuple([v.split("'")[1] for v in input.split(',')])

            while True:
                data = split(next(cursor))
                if data is None:            # Database cleared.
                    self.exit()
                elif data[3] not in StationInfo:
                    warnings.warn('unregistered station name.', UserWarning)
                else:
                    break
            data_dict = extract_data(data)
            return data_dict['datetime'], data_dict

        def ltgpos_rpc(data: List[dict]) -> None:
            # TODO Deduplicate and sort
            if len(data) < 3:
                return
            data_json = json.dumps(data)
            print(data_json)

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
                ltgpos_rpc(data_batch)
                data_batch = None


if __name__ == '__main__':
    args = parse_args()
    with open(args.input_file) as f:
        server = RpcClient(f)
        server.loop()
