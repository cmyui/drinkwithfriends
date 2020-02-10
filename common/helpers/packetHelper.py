from typing import Any, Dict, Tuple, Optional
from common.constants import dataTypes, packetID
from struct import pack as _pack, unpack as _unpack

class Packet(object):
    def __init__(self, id: int = None):
        self.id: Optional[int] = id
        self.data: bytearray = bytearray()
        self.length = 0

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

            fmt: str = ''

            # hahaha what's a switchcase
            if type == dataTypes.PAD_BYTE:    fmt = 'x'
            elif type == dataTypes.SHORT:     fmt = 'h'
            elif type == dataTypes.USHORT:    fmt = 'H'
            elif type == dataTypes.INT:       fmt = 'i'
            elif type == dataTypes.UINT:      fmt = 'I'
            elif type == dataTypes.LONG:      fmt = 'l'
            elif type == dataTypes.ULONG:     fmt = 'L'
            elif type == dataTypes.LONGLONG:  fmt = 'q'
            elif type == dataTypes.ULONGLONG: fmt = 'Q'
            elif type == dataTypes.FLOAT:     fmt = 'f'
            elif type == dataTypes.DOUBLE:    fmt = 'd'

            if not fmt:
                print(f'[WARN] Unknown dataType {type}.')
                continue

            self.data += _pack(fmt, data)
        return

    def read_data(self, data) -> Dict[str, Any]:
        self.data = data

        from timeit import timeit
        timeit('self.id, self.length = _unpack("hi", self.data)', number=10000)
        timeit('self.id, self.length = _unpack("hi", self.data[0:5])', number=10000)
        self.id, self.length = _unpack('hi', self.data)
        #return {
        #    'id': self.id,
        #    'length': len
        #}
