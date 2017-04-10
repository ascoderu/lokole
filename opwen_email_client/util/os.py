from ast import literal_eval
from os import getenv as _getenv
from os import listdir
from os.path import isdir
from os.path import join
from typing import Iterable
from typing import TypeVar

T = TypeVar('T')


def getenv(key: str, default: T=None) -> T:
    value = _getenv(key, default)
    try:
        return literal_eval(value)
    except (ValueError, SyntaxError):
        return value


def subdirectories(root: str) -> Iterable[str]:
    try:
        return (sub for sub in listdir(root) if isdir(join(root, sub)))
    except OSError:
        return []
