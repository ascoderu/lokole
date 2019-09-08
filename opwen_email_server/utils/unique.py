from hashlib import sha256
from uuid import uuid4

from opwen_email_server.utils.serialization import to_msgpack_bytes


def new_email_id(email: dict) -> str:
    return sha256(to_msgpack_bytes(email)).hexdigest()


def new_client_id() -> str:
    return str(uuid4())


def new_resource_id() -> str:
    return str(uuid4())
