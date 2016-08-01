from contextlib import contextmanager
from os import path
from os import remove
from shutil import rmtree
from tempfile import NamedTemporaryFile
from tempfile import mkdtemp


def _remove(filepath):
    """
    :type filepath: str

    """
    if path.isdir(filepath):
        rmtree(filepath)
    elif path.isfile(filepath):
        remove(filepath)


@contextmanager
def create_temporary_directory(delete=True):
    """
    :type delete: bool

    """
    directory = mkdtemp()

    yield directory

    if delete:
        rmtree(directory)


@contextmanager
def removing(filepath):
    """
    :type filepath: str

    """
    yield filepath
    _remove(filepath)


class SafeNamedTemporaryFile(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.fobj = None

    def __enter__(self):
        self.fobj = NamedTemporaryFile(*self.args, **self.kwargs)
        return self.fobj

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            _remove(self.fobj.name)
