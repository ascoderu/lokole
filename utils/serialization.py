import json
import zlib
from gzip import GzipFile
from io import BytesIO


def _compress(data, level):
    """
    :type data: bytes
    :type level: int
    :rtype: bytes

    """
    with BytesIO() as fobj:
        with GzipFile(fileobj=fobj, mode='wb', compresslevel=level) as gzfobj:
            gzfobj.write(data)
        fobj.seek(0)
        compressed_data = fobj.read()
    return compressed_data


def _decompress(compressed):
    """
    :type compressed: bytes
    :rtype: bytes

    """
    try:
        return zlib.decompress(compressed, 16 + zlib.MAX_WBITS)
    except zlib.error as error:
        raise ValueError('unable to decompress') from error


class CompressedJson(object):
    ENCODING = 'utf8'

    def __init__(self, level=9):
        """
        :type level: int

        """
        self.level = level

    def serialize(self, obj):
        """
        :type obj: object
        :rtype: bytes

        """
        if not obj:
            return b''

        serialized = json.dumps(obj)
        serialized_bytes = serialized.encode(self.ENCODING)
        return _compress(serialized_bytes, level=self.level)

    def deserialize(self, compressed):
        """
        :type compressed: bytes
        :rtype: object

        """
        if not compressed:
            return None

        try:
            serialized_bytes = _decompress(compressed)
            serialized = serialized_bytes.decode(self.ENCODING)
            return json.loads(serialized)
        except (UnicodeDecodeError, ValueError):
            return None
