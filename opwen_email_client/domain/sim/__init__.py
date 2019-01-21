from pathlib import Path
from subprocess import Popen  # nosec
from tempfile import NamedTemporaryFile
from time import sleep
from typing import IO


def _dialer_is_connected(log_path: str) -> bool:
    with open(log_path, 'rb') as fobj:
        for line in fobj:
            if line.startswith(b'--> secondary DNS address'):
                return True
    return False


def _start_dialer(config: Path, log_file: IO) -> Popen:
    return Popen(['/usr/bin/wvdial',
                  '--config', str(config.absolute())],
                 stderr=log_file)


def dialup(config: Path, max_retries: int, poll_seconds: int) -> Popen:
    with NamedTemporaryFile(prefix='wvdial', suffix='.log') as log:
        connection = _start_dialer(config, log)

        while not _dialer_is_connected(log.name):
            if connection.poll() is not None:
                connection.terminate()
                raise ValueError('Invalid wvdial configuration')

            if max_retries <= 0:
                connection.terminate()
                raise ValueError('Modem taking too long to connect')

            sleep(poll_seconds)
            max_retries -= 1

        return connection
