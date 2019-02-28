from os import environ
from typing import Dict
from typing import Optional
from urllib.parse import quote


class Env(object):
    def __init__(self, env: Optional[Dict[str, str]] = None):
        self._env = env or environ

    def __call__(self, name: str, default: str = '') -> str:
        return self._env.get(name, default)

    def integer(self, name: str, default: int = 0) -> int:
        return int(self(name, str(default)))

    def boolean(self, name, default: bool = False) -> bool:
        return self(name, str(default)) == str(True)

    def urlpart(self, name: str, default: str = '') -> str:
        return quote(self(name, default), safe='')
