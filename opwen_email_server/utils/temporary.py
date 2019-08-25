from contextlib import contextmanager
from contextlib import suppress
from os import remove
from os.path import join
from tempfile import gettempdir
from typing import Generator
from typing import Optional
from uuid import uuid4

from opwen_email_server.utils.path import get_extension


def create_tempfilename(suffix: Optional[str] = None) -> str:
    extension = get_extension(suffix)
    return join(gettempdir(), f'{uuid4()}{extension}')


@contextmanager
def removing(path: str) -> Generator[str, None, None]:
    try:
        yield path
    finally:
        remove_if_exists(path)


def remove_if_exists(path: str):
    with suppress(FileNotFoundError):
        remove(path)
