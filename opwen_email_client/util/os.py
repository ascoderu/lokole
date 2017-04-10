from ast import literal_eval
from os import getenv as _getenv
from os import listdir
from os.path import isdir
from os.path import join


def getenv(key, default=None):
    """
    :type key: str
    :type default: T
    :rtype: T

    """
    value = _getenv(key, default)
    try:
        return literal_eval(value)
    except (ValueError, SyntaxError):
        return value


def subdirectories(root):
    """
    :type root: str
    :rtype: collections.Iterable[str]

    """
    try:
        return (sub for sub in listdir(root) if isdir(join(root, sub)))
    except OSError:
        return []
