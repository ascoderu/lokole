from gzip import GzipFile
from io import BytesIO
from json import JSONDecodeError
from json import dumps
from json import loads
from typing import Optional


def from_json(obj: str) -> dict:
    return loads(obj)


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


def to_json(obj: object) -> str:
    return dumps(obj, separators=(',', ':'))


def to_jsonl_bytes(obj) -> bytes:
    return to_json(obj).encode('utf-8') + b'\n'


def gzip_string(uncompressed: str) -> bytes:
    uncompressed_bytes = uncompressed.encode()
    stream = BytesIO()
    with GzipFile(fileobj=stream, mode='wb') as fobj:
        fobj.write(uncompressed_bytes)  # type: ignore
    stream.seek(0)
    compressed = stream.read()
    return compressed


def gunzip_string(compressed: bytes) -> str:
    stream = BytesIO()
    stream.write(compressed)
    stream.seek(0)
    with GzipFile(fileobj=stream, mode='rb') as fobj:
        uncompressed_bytes = fobj.read()  # type: ignore
    uncompressed = uncompressed_bytes.decode()
    return uncompressed
