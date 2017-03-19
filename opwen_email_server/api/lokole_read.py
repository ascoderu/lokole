from typing import Tuple
from typing import Union

from opwen_email_server.services.auth import EnvironmentAuth

CLIENTS = EnvironmentAuth()


def download(client_id: str) -> Union[dict, Tuple[str, int]]:
    if client_id not in CLIENTS:
        return 'client is not registered', 403

    return {
        'resource_id': None,
        'resource_type': None,
    }
