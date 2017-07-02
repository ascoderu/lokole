from typing import Tuple
from uuid import uuid4

from opwen_email_server import config
from opwen_email_server.services.auth import AzureAuth
from opwen_email_server.services.queue import AzureQueue
from opwen_email_server.services.storage import AzureTextStorage

STORAGE = AzureTextStorage(account=config.STORAGE_ACCOUNT,
                           key=config.STORAGE_KEY,
                           container=config.CONTAINER_SENDGRID_MIME)

QUEUE = AzureQueue(account=config.STORAGE_ACCOUNT, key=config.STORAGE_KEY,
                   name=config.QUEUE_SENDGRID_MIME)

CLIENTS = AzureAuth(account=config.STORAGE_ACCOUNT, key=config.STORAGE_KEY,
                    table=config.TABLE_AUTH)


class _Receiver(object):
    def __call__(self, client_id: str, email: str) -> Tuple[str, int]:
        if not CLIENTS.domain_for(client_id):
            return 'client is not registered', 403

        email_id = str(uuid4())

        STORAGE.store_text(email_id, email)

        QUEUE.enqueue({
            '_version': '0.1',
            '_type': 'mime_email_received',
            'resource_id': email_id,
            'container_name': STORAGE.container,
        })

        return 'received', 200


receive = _Receiver()
