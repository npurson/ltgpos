import warnings

from collections import namedtuple


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


def convert_slice(path: str):
    """Converts binary number from SLICE file to decimal number."""

    def bin2vec(bin: str) -> int:
        """TODO"""
        ...

    with open(path, 'rb') as f:
        data = f.read()[24:]
        decs = []
        while data:
            decs.append(bin2vec(data[:2]))
            data = data[2:]
    return


'''
def process(self):
    with open(self.filePath, 'rb') as f:
        f.read(24)
        data = f.read(2)
        while data:
            # get the validBit
            dataStr = bin(int.from_bytes(data, 'big'))[2:]
            self.data.append(self.convert(data, len(dataStr) + 1))
            data = f.read(2)
    return

def convert(self, data, nValidateBit=16):
    data = int.from_bytes(data, 'big', signed=False)

    if data is None or not data:
        return 0
    if nValidateBit > 16:
        return 0

    mask = 0xffff >> (16 - nValidateBit + 1)
    # TODO：
    # 1. 目前数据和机器数据都是小字节序，没做额外操作进行修改
    # 2. 数据一次读入内存，没有分批读取

    nOffsetValue = data
    nReturnValue = 0
    fvalue = 0
    i = 1
    tmp1 = 1 << (nValidateBit - 1)
    if nOffsetValue & (1 << (nValidateBit - 1)):
        i = 1
    else:
        i = -1
    tmp2 = nOffsetValue & (1 << (nValidateBit - 1))
    nOffsetValue = nOffsetValue & mask

    if i == 1:
        nReturnValue = nOffsetValue
    elif nOffsetValue == 0:
        nReturnValue = i*(1 << (nValidateBit - 1))
    else:
        nReturnValue = ~(nOffsetValue - 1)
        nReturnValue = (nReturnValue & 0xffff)
        nReturnValue = nReturnValue & mask
        nReturnValue = i * nReturnValue

    nReturnValue = nReturnValue * (-1)
    fvalue = (float(nReturnValue)) / 8192 * 10 * 1000
    nReturnValue = int(fvalue)

    return nReturnValue

SHORT CBinToSampleData::ConvertOffsetBinaryToTrueCode(PSHORT pOffsetBinaryData,LONG nValidateBit)
{
	/*
	偏移二进制码转化为正常数值：
	偏移二进制码：为补码符号位取反；
	补码：正数，符号位为0，数值位和原码相同；负数：符号位为1，数值位求反加1；
	可推断偏移二进制码计算过程：
	首先判断最高位，0为负数，1为正数，然后数值位：如果是负数，减1，求反；正数不变
	*/

	if (pOffsetBinaryData == NULL)
		return 0;
	if (nValidateBit > 16)
		return 0;
	USHORT nMask =  (0xffff >> (16 - nValidateBit + 1));
	SHORT nOffsetValue = ntohs(*pOffsetBinaryData);//如果原始字节序不需要转换，可以省略掉此处代码
	SHORT nReturnValue = 0;
	FLOAT fValue = 0;

	INT i = 1;
	if (nOffsetValue & (1 << (nValidateBit - 1)))//符号位为1 代表正数，
	{
		i = 1;
	}
	else
	{
		i = -1;
	}

	nOffsetValue = nOffsetValue & nMask;//去掉符号位和其他无效bit；

	if(i == 1)
	{
		nReturnValue =  i*nOffsetValue;
	}
	else if(nOffsetValue == 0)//如果是负数，并且数值位为0，则为
	{
		nReturnValue = i*(1 << (nValidateBit - 1));
	}
	else
	{
		nReturnValue = ~(nOffsetValue - 1);
		nReturnValue = nReturnValue & nMask;//去掉高位无效bit；
		nReturnValue =  i*nReturnValue;
	}
	nReturnValue = nReturnValue*(-1);//极性做一次变化。
	fValue = ((FLOAT)nReturnValue)/8192*10*1000;//数值转换成毫伏
	nReturnValue = (SHORT)fValue;
	return nReturnValue;
}
'''


if __name__ == '__main__':
    import pdb; pdb.set_trace()
