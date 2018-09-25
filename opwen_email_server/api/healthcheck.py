from typing import Tuple


class _Pinger(object):
    def __call__(self) -> Tuple[str, int]:
        return 'OK', 200


ping = _Pinger()
