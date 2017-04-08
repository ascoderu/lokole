from typing import Tuple
from typing import Union

from opwen_email_server import config
from opwen_email_server.services import server_datastore
from opwen_email_server.services.auth import EnvironmentAuth
from opwen_email_server.services.storage import AzureFileStorage
from opwen_email_server.services.storage import AzureObjectStorage

STORAGE = AzureObjectStorage(
    AzureFileStorage(account=config.CLIENT_STORAGE_ACCOUNT,
                     key=config.CLIENT_STORAGE_KEY,
                     container=config.CONTAINER_CLIENT_PACKAGES))

CLIENTS = EnvironmentAuth()


def download(client_id: str) -> Union[dict, Tuple[str, int]]:
    if client_id not in CLIENTS:
        return 'client is not registered', 403

    domain = CLIENTS.domain_for(client_id)
    delivered = set()

    def mark_delivered(email: dict) -> dict:
        delivered.add(email['_uid'])
        return email

    pending = server_datastore.fetch_pending_emails(domain)
    pending = map(mark_delivered, pending)

    resource_id = STORAGE.store_objects(pending)
    server_datastore.mark_emails_as_delivered(domain, delivered)

    return {
        'resource_id': resource_id,
        'resource_container': STORAGE.container,
        'resource_type': 'azure-blob',
    }
