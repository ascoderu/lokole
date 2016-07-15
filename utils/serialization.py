import json
import zlib


class CompressedJson(object):
    ENCODING = 'utf8'

    def __init__(self, level=9):
        self.level = level

    def serialize(self, obj):
        if not obj:
            return b''

        serialized = json.dumps(obj)
        serialized_bytes = serialized.encode(self.ENCODING)
        return zlib.compress(serialized_bytes, self.level)

    def deserialize(self, compressed):
        if not compressed:
            return u''

        serialized_bytes = zlib.decompress(compressed)
        serialized = serialized_bytes.decode(self.ENCODING)
        return json.loads(serialized)
