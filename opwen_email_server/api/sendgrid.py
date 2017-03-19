from uuid import uuid4

from opwen_email_server.api import config
from opwen_email_server.services.queue import AzureQueue
from opwen_email_server.services.storage import AzureStorage

STORAGE = AzureStorage(account=config.STORAGE_ACCOUNT, key=config.STORAGE_KEY,
                       container='SendgridInboundEmails')

QUEUE = AzureQueue(account=config.STORAGE_ACCOUNT, key=config.STORAGE_KEY,
                   name='SengridInboundEmails')


def receive(email: str):
    email_id = str(uuid4())

    STORAGE.store_text(email_id, email)

    QUEUE.enqueue({
        '_version': '0.1',
        '_type': 'mime_email_received',
        '_received_by': 'sendgrid',
        'resource_id': email_id,
        'container_name': STORAGE.container,
    })
