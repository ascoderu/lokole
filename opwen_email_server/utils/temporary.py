from contextlib import contextmanager
from contextlib import suppress
from os import remove
from os.path import join
from tempfile import gettempdir
from typing import Generator
from uuid import uuid4


def create_tempfilename() -> str:
    return join(gettempdir(), str(uuid4()))


@contextmanager
def removing(path: str) -> Generator[str, None, None]:
    try:
        yield path
    finally:
        remove_if_exists(path)


def remove_if_exists(path: str):
    with suppress(FileNotFoundError):
        remove(path)
