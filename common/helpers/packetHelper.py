from typing import Any, Dict, List, Tuple, Optional, Union
from common.constants import dataTypes, packets
from common.objects.user import User
from struct import pack as _pack, unpack as _unpack, calcsize

# testing
from inspect import currentframe, getframeinfo

class Packet(object):
    def __init__(self, id: Optional[int] = None):
        self.id: Optional[int] = id
        #self.data: bytearray = bytearray()
        self.data: bytes = b''
        self.length = 0

        self.offset = 0 # only used for unpacking
        return

    def __enter__(self):
        return self

    def __exit__(self, *args):
        del self
        return

    def get_data(self) -> bytes:
        """
        Return the request in HTTP format.
        This should be used in the final step of sending data to the client.
        """
        self.data = _pack('<hh', self.id, len(self.data)) + self.data # ew?
        return f'HTTP/1.1 200 OK\r\nContent-Length: {len(self.data)}\r\n\r\n'.encode() + self.data

    def pack_data(self, _data: List[List[Union[List[int], int, str, float, User]]]) -> None:
        """
        Pack `_data` into `self.data`.

        Data should be passed into this function in the format as followed:
        [
          (data, data_type),
          ...
        ]
        """
        for data, type in _data:
            if type in [dataTypes.INT16_LIST, dataTypes.INT32_LIST]:
                self.data += data.__len__().to_bytes(1, 'little')
                for i in data: self.data += i.to_bytes(2 if type == dataTypes.INT16_LIST else 4, 'little')
            elif type == dataTypes.STRING: self.data += (b'\x0b' + data.__len__().to_bytes(1, 'little') + data.encode()) if data else b'\x00'
            elif type == dataTypes.USERINFO_LIST:
                self.data += data.__len__().to_bytes(1, 'little')
                for u in data: self.data += _pack('<h', u[0]) + u[1].__len__().to_bytes(1, 'little') + u[1].encode() + _pack('<h', u[2])
            elif type == dataTypes.USERINFO: self.data += _pack('<h', data[0]) + data[1].__len__().to_bytes(1, 'little') + data[1].encode() + _pack('<h', data[2])
            else:
                fmt: str = self.get_fmtstr(type)
                if not fmt: continue
                else: fmt = f'<{fmt}'
                self.data += _pack(fmt, data)
        return


    def unpack_data(self, types: List[int]) -> Tuple[Any]: # TODO: return type
        """
        Unpack `self.data` one var at a time from with the types from `types`.

        Types should be passed in the format as follows:
        [
           dataTypes.INT32,
           ...
        ]
        """
        unpacked: List[Any] = []
        for type in types:
            if type in [dataTypes.INT16_LIST, dataTypes.INT32_LIST]:
                l: List[int] = []

                length: int = self.data[self.offset]
                self.offset += 1

                size: int = 2 if dataTypes.INT16_LIST else 4
                for _ in range(0, length):
                    l.extend(_unpack('<h' if dataTypes.INT16_LIST else '<i', self.data[self.offset:self.offset + size]))
                    self.offset += size

                unpacked.append(tuple(l))
                del l
            elif type == dataTypes.STRING: # cant be cheap this time :(
                if self.data[self.offset] == 11: # String exists
                    self.offset += 1
                    length: int = self.data[self.offset]
                    self.offset += 1
                    unpacked.append(self.data[self.offset:self.offset + length].decode())
                    self.offset += length
                else: self.offset += 1
            elif type == dataTypes.USERINFO_LIST:
                #l: List[User] = []
                length: int = self.data[self.offset]
                self.offset += 1

                for _ in range(0, length):
                    #l.extend(_unpack('<h', self.data[self.offset:self.offset + 2]))
                    #self.offset += 2
                    #length: int = self.data[self.offset]
                    #self.offset += 1
                    #l.append(self.data[self.offset:self.offset + length].decode())
                    #self.offset += length
                    #l.extend(_unpack('<h', self.data[self.offset:self.offset + 2]))
                    #self.offset += 2
                    unpacked.append([ # because fuck u i feel like it
                        *_unpack('<h', self.data[self.offset:self.offset + 2]),
                        self.data[self.offset + 3: self.offset + 3 + self.data[self.offset + 2]].decode(),
                        *_unpack('<h', self.data[self.offset + 3 + self.data[self.offset + 2]:self.offset + 3 + self.data[self.offset + 2] + 2])
                    ])
                    self.offset += 3 + self.data[self.offset + 2] + 2
                    #l.append([ # because fuck u i feel like it
                    #    *_unpack('<h', self.data[self.offset:self.offset + 2]),
                    #    self.data[self.offset + 3: self.offset + 3 + self.data[self.offset + 2]].decode(),
                    #    *_unpack('<h', self.data[self.offset + 3 + self.data[self.offset + 2]:self.offset + 3 + self.data[self.offset + 2] + 2])
                    #])
                #unpacked.append(tuple(l))
                #del l
            elif type == dataTypes.USERINFO:
                unpacked.append(_unpack('<h', self.data[self.offset:self.offset + 2])) # userid
                self.offset += 2

                length: int = self.data[self.offset] # username (note: '\x0b' byte is not sent here)
                self.offset += 1
                unpacked.append(self.data[self.offset:self.offset + length].decode())
                self.offset += length

                unpacked.append(_unpack('<h', self.data[self.offset:self.offset + 2])) # privileges
            else:
                fmt: str = self.get_fmtstr(type)
                if not fmt: continue
                else: fmt = f'<{fmt}'
                unpacked.extend([x for x in _unpack(fmt, self.data[self.offset:self.offset + calcsize(fmt)])])
                self.offset += calcsize(fmt)

        return tuple(unpacked)
    def read_data(self, data) -> None:
        self.data = data

        size: int = calcsize('<hh')
        self.id, self.length = _unpack('<hh', self.data[self.offset:self.offset + size])
        self.offset += size
        del size
        return

    @staticmethod
    def get_fmtstr(type: int) -> Optional[str]:
        #if type in [
        #    dataTypes.INT32_LIST,
        #    dataTypes.INT16_LIST,
        #    dataTypes.STRING
        #]: return
        #elif type == dataTypes.PAD_BYTE: return 'x'
        if type == dataTypes.INT16: return 'h'
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
        self.raw: List[bytes] = data.split(b'\r\n\r\n', maxsplit=1)
        self.parse_headers(self.raw[0].decode().split('\r\n'))
        self.body: bytes = self.raw[1]
        return

    def parse_headers(self, _headers: bytes) -> None:
        self.headers: Dict[str, str] = {}
        for line in _headers:
            if ':' not in line: continue
            k, v = line.split(':')
            self.headers[k] = v.lstrip()
        return
