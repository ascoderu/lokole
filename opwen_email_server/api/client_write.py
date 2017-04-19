from typing import Tuple

from connexion import request

from opwen_email_server import config
from opwen_email_server.services.auth import EnvironmentAuth
from opwen_email_server.services.queue import AzureQueue

QUEUE = AzureQueue(account=config.STORAGE_ACCOUNT, key=config.STORAGE_KEY,
                   name=config.QUEUE_CLIENT_PACKAGE)

CLIENTS = EnvironmentAuth()


def upload(upload_info: dict) -> Tuple[str, int]:
    client_id = request.headers['X-LOKOLE-ClientId']
    if client_id not in CLIENTS:
        return 'client is not registered', 403

    resource_type = upload_info.get('resource_type')
    resource_id = upload_info.get('resource_id')
    resource_container = upload_info.get('resource_container')

    QUEUE.enqueue({
        '_version': '0.1',
        '_type': 'lokole_emails_received',
        '_resource_type': resource_type,
        'resource_id': resource_id,
        'container_name': resource_container,
    })

    return 'uploaded', 200
