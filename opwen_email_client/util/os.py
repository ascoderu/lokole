from os import listdir
from os.path import isdir
from os.path import join


def subdirectories(root):
    """
    :type root: str
    :rtype: collections.Iterable[str]

    """
    try:
        return (sub for sub in listdir(root) if isdir(join(root, sub)))
    except OSError:
        return []
