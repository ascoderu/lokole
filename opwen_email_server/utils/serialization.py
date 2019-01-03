from base64 import b64decode
from base64 import b64encode
from gzip import GzipFile
from io import BytesIO
from json import JSONDecodeError
from json import dumps
from json import loads
from typing import Optional

from msgpack import packb as msgpack_dump
from msgpack import unpackb as msgpack_load


def to_json(obj: object) -> str:
    return dumps(obj, separators=(',', ':'))


def from_json(obj: str) -> dict:
    return loads(obj)


def to_jsonl_bytes(obj) -> bytes:
    return to_json(obj).encode('utf-8') + b'\n'


def from_jsonl_bytes(obj: bytes) -> Optional[dict]:
    try:
        decoded = obj.decode('utf-8')
    except UnicodeDecodeError:
        return None
    decoded = decoded.rstrip(',\n')
    try:
        return from_json(decoded)
    except JSONDecodeError:
        return None


def to_msgpack_bytes(obj) -> bytes:
    encoded = msgpack_dump(obj, use_bin_type=True)
    return encoded + b'\n'


def from_msgpack_bytes(serialized: bytes) -> dict:
    encoded = serialized.rstrip(b'\n')
    return msgpack_load(encoded, raw=False)


def to_base64(content: bytes) -> str:
    return b64encode(content).decode('ascii')


def from_base64(encoded: str) -> bytes:
    return b64decode(encoded)


def gzip_bytes(uncompressed_bytes: bytes) -> bytes:
    stream = BytesIO()
    with GzipFile(fileobj=stream, mode='wb') as fobj:
        fobj.write(uncompressed_bytes)  # type: ignore
    stream.seek(0)
    compressed = stream.read()
    return compressed


def gunzip_bytes(compressed: bytes) -> bytes:
    stream = BytesIO()
    stream.write(compressed)
    stream.seek(0)
    with GzipFile(fileobj=stream, mode='rb') as fobj:
        uncompressed_bytes = fobj.read()  # type: ignore
    return uncompressed_bytes
