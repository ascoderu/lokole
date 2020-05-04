from hashlib import sha256
from random import Random
from typing import Optional
from uuid import UUID
from uuid import uuid4

from opwen_email_server.utils.serialization import to_msgpack_bytes


class NewGuid:
    def __init__(self, seed: Optional[int] = None) -> None:
        self._random = None  # type: Optional[Random]

        if seed is not None:
            self._random = Random()
            self._random.seed(seed)

    def __call__(self) -> str:
        if self._random is not None:
            guid = UUID(int=self._random.getrandbits(128))
        else:
            guid = uuid4()

        return str(guid)


def new_email_id(email: dict) -> str:
    return sha256(to_msgpack_bytes(email)).hexdigest()
