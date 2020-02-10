from typing import Any, Dict, List, Tuple, Optional
from common.constants import dataTypes, packetID
from struct import pack as _pack, unpack as _unpack, calcsize

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

    def pack_data(self, _data: Tuple[Any]) -> None:
        # Pack data passed in the format:
        # ((data, data_type), ...)
        for data, type in _data:
            if type == dataTypes.STRING: # Cheap ass ULEB128
                self.data += b'\x0b' + len(data).to_bytes(1, 'little') + data.encode()
                continue

            fmt: str = self.get_fmtstr(type)
            if not fmt: continue

            self.data += _pack(fmt, data)
        return

    def unpack_data(self, types) -> Tuple[Any]: # TODO: return type
        unpacked: List[Any] = []
        for type in types:
            if type == dataTypes.STRING: # cant be cheap this time :(
                if self.data[self.offset] == 11: # String exists
                    self.offset += 1

                    length: int = self.data[self.offset]
                    self.offset += 1

                    unpacked.append(self.data[self.offset:self.offset + length].decode())
                    self.offset += length

                else:
                    print(f'invalid str - {self.data} - {self.data[self.offset]}')
                    self.offset += 1
                continue

            fmt: str = self.get_fmtstr(type)
            if not fmt: continue
            unpacked.append(*[x for x in _unpack(f'<{fmt}', self.data[self.offset:self.offset + calcsize(fmt)])])
            self.offset += calcsize(fmt)

        return tuple(unpacked)

    def read_data(self, data) -> None:
        self.data = bytearray(data.encode())
        self.id, self.length = _unpack('<hi', self.data[self.offset:self.offset + 6]) # calcsize('<hi')
        self.offset += 6#calcsize('<hi')
        return

    @staticmethod
    def get_fmtstr(type: int) -> Optional[str]:
        if type == dataTypes.STRING: return None
        elif type == dataTypes.PAD_BYTE: return 'x'
        elif type == dataTypes.SHORT: return 'h'
        elif type == dataTypes.USHORT: return 'H'
        elif type == dataTypes.INT: return 'i'
        elif type == dataTypes.UINT: return 'I'
        elif type == dataTypes.LONG: return 'l'
        elif type == dataTypes.ULONG: return 'L'
        elif type == dataTypes.LONGLONG: return 'q'
        elif type == dataTypes.ULONGLONG: return 'Q'
        elif type == dataTypes.FLOAT: return 'f'
        elif type == dataTypes.DOUBLE: return 'd'
        print(f'[WARN] Unknown dataType {type}.')
        return None
