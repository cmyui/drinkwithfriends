from typing import Any, Dict, List, Tuple, Optional, Union
from common.constants import dataTypes, packets
from common.objects.user import User
from struct import pack as _pack, unpack as _unpack, calcsize

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

        Data should be passed into this function in the format [[data, data_type], ...]
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

        Types should be passed in the format [data_type, ...]
        """
        unpacked: List[Any] = []
        for type in types:
            if type in [dataTypes.INT16_LIST, dataTypes.INT32_LIST]:
                """
                Send a list of integers.

                Format:
                  > 1 byte: length of list
                  > 2/4 bytes: (depending on int16/int32 list) for each int
                """
                l: List[int] = []
                length: int = self.data[self.offset]
                self.offset += 1
                size: int = 2 if dataTypes.INT16_LIST else 4
                for _ in range(length):
                    l.extend(_unpack('<h' if type == dataTypes.INT16_LIST else '<i', self.data[self.offset:self.offset + size]))
                    self.offset += size
                unpacked.append(tuple(l))
                del l
            elif type == dataTypes.STRING: # cant be cheap this time :(
                """
                Pack a string.

                Format:
                  > 1 byte: '\x0b' if string is not empty, '\x00' if empty
                  > 1 byte: length
                  > indef. bytes: our string
                """
                if self.data[self.offset] == 11: # '\x0b
                    self.offset += 1
                    length: int = self.data[self.offset]
                    self.offset += 1
                    unpacked.append(self.data[self.offset:self.offset + length].decode())
                    self.offset += length
                else: self.offset += 1 # '\x00'
            elif type == dataTypes.USERINFO:
                """
                Pack basic information about a user.

                Format:
                  > 2 bytes: userID
                  > 1 byte: length of subsequent usernmae string
                  > indef. bytes: username string
                  > 2 bytes: privileges
                """
                unpacked.append(_unpack('<h', self.data[self.offset:self.offset + 2])) # userid
                self.offset += 2
                length: int = self.data[self.offset] # username (note: '\x0b' byte is not sent here)
                self.offset += 1
                unpacked.append(self.data[self.offset:self.offset + length].decode())
                self.offset += length
                unpacked.append(_unpack('<h', self.data[self.offset:self.offset + 2])) # privileges
            elif type == dataTypes.USERINFO_LIST:
                """
                Pack basic information for multiple users.

                Format:
                  > 1 byte: length of list
                  > indef. bytes: list of `USERINFO` types.
                """
                length: int = self.data[self.offset]
                self.offset += 1
                for _ in range(length):
                    unpacked.append([ # ugly code lol
                        *_unpack('<h', self.data[self.offset:self.offset + 2]),
                        self.data[self.offset + 3: self.offset + 3 + self.data[self.offset + 2]].decode(),
                        *_unpack('<h', self.data[self.offset + 3 + self.data[self.offset + 2]:self.offset + 3 + self.data[self.offset + 2] + 2])
                    ])
                    self.offset += 3 + self.data[self.offset + 2] + 2
            else:
                """
                Pack something using the `struct` library.

                This will be used only for primitive types.
                """
                fmt: str = self.get_fmtstr(type)
                if not fmt: continue
                else: fmt = f'<{fmt}'
                unpacked.extend([x for x in _unpack(fmt, self.data[self.offset:self.offset + calcsize(fmt)])])
                self.offset += calcsize(fmt)

        return tuple(unpacked)

    def read_data(self, data) -> None:
        """
        Read the ID and length of a packet.
        (increments the offset accordingly)
        """
        self.data = data
        size: int = calcsize('<hh')
        self.id, self.length = _unpack('<hh', self.data[self.offset:self.offset + size])
        self.offset += size
        del size
        return

    @staticmethod
    def get_fmtstr(type: int) -> Optional[str]:
        """
        Get the format string for a primitive type from `dataTypes`.
        """
        if   type == dataTypes.INT16:  return 'h'
        elif type == dataTypes.UINT16: return 'H'
        elif type == dataTypes.INT32:  return 'i' # not using long
        elif type == dataTypes.UINT32: return 'I' #
        elif type == dataTypes.INT64:  return 'q'
        elif type == dataTypes.UINT64: return 'Q'
        elif type == dataTypes.FLOAT:  return 'f'
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
        """
        Parse HTTP headers, splitting them into a dictionary.
        """
        self.headers: Dict[str, str] = {}
        for k, v in (line.split(':') for line in _headers if ':' in line):
            self.headers[k] = v.lstrip()
        return
