from gzip import GzipFile
from io import BytesIO
from json import dumps


def to_json(obj: object) -> str:
    return dumps(obj, separators=(',', ':'))


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
