from fileinput import input as fileinput
from gzip import GzipFile
from os import listdir
from os.path import isdir
from os.path import join
from pathlib import Path
from typing import Callable
from typing import Iterable
from typing import Optional
from typing import Union


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


def backup(path: Union[str, Path], suffix: str = '.bak.gz') -> Optional[Path]:
    path = Path(path)

    if not path.is_file():
        return None

    backup_path = '{}{}'.format(path, suffix)
    with GzipFile(backup_path, mode='ab') as fout:
        with path.open('rb') as fin:
            for line in fin:
                fout.write(line)

    return Path(backup_path)
