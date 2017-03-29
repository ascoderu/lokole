from gzip import open as gzip_open
from json import loads
from os import remove
from typing import Iterable

from opwen_email_server import config
from opwen_email_server.services.storage import AzureFileStorage

STORAGE = AzureFileStorage(account=config.CLIENT_STORAGE_ACCOUNT,
                           key=config.CLIENT_STORAGE_KEY,
                           container=config.CONTAINER_CLIENT_PACKAGES)


def unpack_emails(resource_id: str) -> Iterable[dict]:
    temp_filename = STORAGE.fetch_file(resource_id)
    try:
        with gzip_open(temp_filename, 'rb') as fobj:
            for line in fobj:
                payload = line.decode('utf-8')
                email = loads(payload)
                yield email
    finally:
        remove(temp_filename)
