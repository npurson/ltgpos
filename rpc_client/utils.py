import warnings

from collections import namedtuple
from typing import List


Coord = namedtuple('Coord', ('latitude', 'longitude'))


class ConstDict(dict):
    """A Dict whose key-value pairs cannot be modified once inited."""
    def __setitem__(self, k, v):
        warnings.warn('trying to overwrite key-value pairs in a ConstDict', UserWarning)


StationInfo = ConstDict({
    "wuhan1": Coord(30.57981889, 114.3642556),
    "wuhan2": Coord(30.48821667, 114.5574272),
    "wuhan3": Coord(30.71696167, 114.57059),
    "wuhan4": Coord(30.39977361, 114.4480892),
    "wuhan5": Coord(30.48366111, 114.3062194),
    "wuhan6": Coord(30.50992472, 114.3977919),
})


def convert_slice(path: str) -> List[int]:
    """Converts bytes from SLICE file to decimal numbers.
    Each packet is of 1024 bytes, where the first 24 bytes is the header,
    and every 2 bytes of the rest is a offset binary code.
    """
    def bin2vec(comp: bytes) -> int:
        """Convert offset binary code to decimal numbers.
        Offset binary code: 2's complement with the inverse of sign bit.
            n_bits = 15 is the 15th bit == 1 else 14
            Positive if the sign bit is 1, -1 and reversed.
            Negative if the sign bit is 0, unchanged.
        """
        comp = int.from_bytes(comp, 'big')
        n_bits = 15 if comp & 0x8000 else 14
        sign = (comp >> n_bits - 1) ^ 0x1
        mask = (0x1 << 17 - n_bits) - 1 << n_bits - 1   # Mask of non-value bits, including sign bit
        comp = comp | mask if sign else comp & ~mask    # Pads to 2's complement with mask of sign
        comp = int.to_bytes(comp, 2, 'big')
        num = -int.from_bytes(comp, 'big', signed=True)
        return int(num * 1e4 / 8192)

    with open(path, 'rb') as f:
        decs = []
        bins = f.read(1024)
        while bins:
            decs += [bin2vec(bins[2*i+24:2*i+26]) for i in range(500)]
            bins = f.read(1024)
    return decs


if __name__ == '__main__':
    decs = convert_slice('test/wuhan3_210416085731.slice')
    for i in decs:
        print(i)
