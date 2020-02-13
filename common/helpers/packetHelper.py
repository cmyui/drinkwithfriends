from typing import Any, Dict, List, Tuple, Optional, Union
from common.constants import dataTypes, packets
from struct import pack as _pack, unpack as _unpack, calcsize

# testing
from inspect import currentframe, getframeinfo

class Packet(object):
    def __init__(self, id: int = None):
        self.id: Optional[int] = id
        #self.data: bytearray = bytearray()
        self.data: bytes = b''
        self.length = 0

        self.offset = 0 # only used for unpacking
        return

    #@property # Convert to bytestring and return.
    def get_data(self) -> bytes:
        self.data = _pack('<hi', self.id, len(self.data)) + bytes(self.data) # suboptimal as FUCK?
        #self.length = len(self.data)
        return b'HTTP/1.1 200 OK\r\nContent-Length: ' \
             + bytes(str(len(self.data))) + b'\r\n\r\n'     \
             + bytes(self.data)

    def pack_data(self, _data: List[Tuple[Union[List[int], int, str, float]]]) -> None:
        """
        Pack `_data` into `self.data`.

        Data should be passed into this function in the format as followed:
        (
          (data, data_type),
          ...
        )
        """
        for data, type in _data:
            if type in [dataTypes.INT16_LIST, dataTypes.INT32_LIST]:
                self.data.append(data.__len__().to_bytes(1, 'little'))
                for i in data: i.to_bytes(2 if type == dataTypes.INT16_LIST else 4, 'little')
                continue
            elif type == dataTypes.STRING:
                if data:
                    self.data += (11).to_bytes(1, 'little')
                    self.data += data.__len__().to_bytes(1, 'little')
                    self.data += data.encode()
                    #self.data.append(11)
                    #self.data.append(data.__len__())
                    #self.data.extend(map(ord, data))
                    #self.data.append(data.encode())
                    #self.data.append((11).to_bytes(1, 'little') + data.__len__().to_bytes(1, 'little') + data.encode())
                    #self.data += (11).to_bytes(1, 'little') + data.__len__().to_bytes(1, 'little') + data.encode()
                else:
                    self.data += (0).to_bytes(1, 'little')
                    #self.data.append(0)
                continue

            fmt: str = self.get_fmtstr(type)
            if not fmt: continue
            else: fmt = f'<{fmt}'

            #self.data.extend(tmp) # suboptimal as fuck?
            self.data += _pack(fmt, data)
        return


    def unpack_data(self, types: List[int]) -> Tuple[Any]: # TODO: return type
        """
        Unpack `self.data` one var at a time from with the types from `types`.

        Types should be passed in the format as follows:
        (
           dataTypes.INT32,
           ...
        )
        """
        unpacked: List[Any] = []
        for type in types:
            if type in [dataTypes.INT16_LIST, dataTypes.INT32_LIST]:
                l: List[int] = []

                length: int = self.data[self.offset]
                self.offset += 2

                for _ in range(0, length, 2 if dataTypes.INT16_LIST else 4):
                    l.append(_unpack(self.get_fmtstr(dataTypes.INT16), self.data[self.offset:self.offset + 2 if dataTypes.INT16_LIST else 4]))
                    self.offset += 2 if dataTypes.INT16_LIST else 4

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
                    self.offset += 1
            else:
                fmt: str = self.get_fmtstr(type)
                if not fmt:
                    continue
                else: fmt = f'<{fmt}'
                unpacked.extend([x for x in _unpack(fmt, self.data[self.offset:self.offset + calcsize(fmt)])])
                self.offset += calcsize(fmt)

        ret = tuple(unpacked)
        del unpacked
        return ret
    def read_data(self, data) -> None:
        self.data = data

        size = calcsize('<hi')
        self.id, self.length = _unpack('<hi', self.data[self.offset:self.offset + size])
        self.offset += size
        return

    @staticmethod
    def get_fmtstr(type: int) -> Optional[str]:
        if type in [
            dataTypes.INT32_LIST,
            dataTypes.INT16_LIST,
            dataTypes.STRING
        ]: return
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
        return

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
