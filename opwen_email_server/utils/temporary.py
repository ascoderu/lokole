from contextlib import contextmanager
from contextlib import suppress
from os import close
from os import remove
from tempfile import mkstemp
from typing import Generator


def create_tempfilename() -> str:
    file_descriptor, filename = mkstemp()
    close(file_descriptor)
    return filename


@contextmanager
def removing(path: str) -> Generator[str, None, None]:
    try:
        yield path
    finally:
        remove_if_exists(path)


def remove_if_exists(path: str):
    with suppress(FileNotFoundError):
        remove(path)
