from typing import Iterable

from opwen_email_server import config
from opwen_email_server.services.storage import AzureFileStorage
from opwen_email_server.services.storage import AzureObjectStorage

STORAGE = AzureObjectStorage(
    AzureFileStorage(account=config.CLIENT_STORAGE_ACCOUNT,
                     key=config.CLIENT_STORAGE_KEY,
                     container=config.CONTAINER_CLIENT_PACKAGES))


def unpack_emails(resource_id: str) -> Iterable[dict]:
    return STORAGE.fetch_objects(resource_id)
