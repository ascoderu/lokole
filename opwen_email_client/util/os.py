from fileinput import input as fileinput
from os import listdir
from os.path import isdir
from os.path import join
from typing import Callable
from typing import Iterable


def subdirectories(root: str) -> Iterable[str]:
    try:
        return (sub for sub in listdir(root) if isdir(join(root, sub)))
    except OSError:
        return []


def replace_line(path: str, match: Callable[[str], bool], replacement: str):
    for line in fileinput(path, inplace=True):
        if match(line):
            end = ''
            if line.endswith('\r\n'):
                end = '\r\n'
            elif line.endswith('\n'):
                end = '\n'
            if replacement.endswith(end):
                end = ''
            print(replacement, end=end)
        else:
            print(line, end='')
