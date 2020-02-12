from typing import Any, Dict, List, Tuple, Optional, Union
from common.constants import dataTypes, packets
from struct import pack as _pack, unpack as _unpack, calcsize

# testing
from inspect import currentframe, getframeinfo

class Packet(object):
    def __init__(self, id: int = None):
        self.id: Optional[int] = id
        self.data: bytearray = bytearray()
        self.length = 0

        self.offset = 0 # only used for unpacking
        return

    @property # Convert to bytestring and return.
    def get_data(self) -> bytes:
        self.data = _pack('<hi', self.id, len(self.data)) + self.data # suboptimal as FUCK?
        #self.data.insert(0, _pack('<hi', self.id, len(self.data)))
        return b'HTTP/1.1 200 OK\r\nContent-Length: '     \
             + str(len(self.data)).encode() + b'\r\n\r\n' \
             + bytes(self.data)

    def pack_data(self, _data: List[Tuple[Union[List[int], int, str, float]]]) -> None:
        # Pack data passed in the format:
        # ((data, data_type), ...)
        print(f'{getframeinfo(currentframe()).lineno}: {_data}')
        for data, type in _data:
            if type == dataTypes.INT_LIST:
                self.data += len(data).to_bytes(1, 'little')
                for i in data:
                    print(f'yeyaeyayea: {i}')
                    self.data += _pack(self.get_fmtstr(dataTypes.INT16), i)
                continue
            elif type == dataTypes.STRING: # Cheap ass ULEB128
                self.data += b'\x0b' + len(data).to_bytes(1, 'little') + data.encode()
                continue

            fmt: str = self.get_fmtstr(type)
            if not fmt: continue

            self.data += _pack(fmt, data)
        return

    def unpack_data(self, types: List[int]) -> Tuple[Any]: # TODO: return type
        unpacked: List[Any] = []
        for type in types:
            if type == dataTypes.INT_LIST:
                l: List[int] = []

                print(f'\n\nNOW\n{self.data}\n\n')
                length: int = self.data[self.offset]
                self.offset += 1

                #l.extend([int.from_bytes(self.data[self.offset:self.offset + 2], 'little') for _ in range(length)])


                print(f'\nBEFORE\n{self.data}\n')
                for _ in range(length):
                    l.append(_unpack(self.get_fmtstr(dataTypes.INT16), self.data[self.offset:self.offset + 2]))
                    #print(int.from_bytes(self.data[self.offset:self.offset + 2], 'little'))
                    #l.append(int.from_bytes(self.data[self.offset:self.offset + 2], 'little'))
                    self.offset += 2
                print(f'\nAFTER\n{self.data}\n')

                print(f'l: {l}')
                unpacked.append(l)
                del l
            elif type == dataTypes.STRING: # cant be cheap this time :(
                if self.data[self.offset] == 11: # String exists
                    self.offset += 1

                    length: int = self.data[self.offset]
                    self.offset += 1

                    unpacked.append(self.data[self.offset:self.offset + length].decode())
                    self.offset += length

                else:
                    print(f'invalid str - {self.data} - {self.data[self.offset]}')
                    self.offset += 1
            else:
                fmt: str = self.get_fmtstr(type)
                if not fmt:
                    print('HERE')
                    continue
                print(f'fmt: {fmt}')
                unpacked.extend([x for x in _unpack(f'<{fmt}', self.data[self.offset:self.offset + calcsize(fmt)])])
                self.offset += calcsize(fmt)
            print(f'DATYPE {type}: {self.data}')

        ret = tuple(unpacked)
        del unpacked
        return ret
    def read_data(self, data) -> None:
        self.data = bytearray(data)
        self.id, self.length = _unpack('<hi', self.data[self.offset:self.offset + calcsize('<hi')])
        self.offset += calcsize('<hi')
        return

    @staticmethod
    def get_fmtstr(type: int) -> Optional[str]:
        if type in [dataTypes.INT_LIST, dataTypes.STRING]: return None
        #elif type == dataTypes.PAD_BYTE: return 'x'
        elif type == dataTypes.INT16: return 'h'
        elif type == dataTypes.UINT16: return 'H'
        elif type == dataTypes.INT32: return 'i'
        elif type == dataTypes.UINT32: return 'I'
        #elif type == dataTypes.INT32: return 'l'
        #elif type == dataTypes.UINT32: return 'L'
        elif type == dataTypes.INT64: return 'q'
        elif type == dataTypes.UINT64: return 'Q'
        elif type == dataTypes.FLOAT: return 'f'
        elif type == dataTypes.DOUBLE: return 'd'
        print(f'[WARN] Unknown dataType {type}.')
        return None

class Connection(object):
    def __init__(self, data: bytes) -> None:
        self.raw: List[bytes] = data.split(b'\r\n\r\n', maxsplit = 1)
        self.headers: Dict[str, str] = {}
        self.parse_headers(self.raw[0].decode().split('\r\n'))
        self.body: bytes = self.raw[1]
        return

    def parse_headers(self, _headers: bytes) -> None:
        for line in _headers:
            if ':' not in line: continue
            k, v = line.split(':')
            self.headers[k] = v.lstrip()
        return
