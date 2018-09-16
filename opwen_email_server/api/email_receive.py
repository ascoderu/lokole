from typing import Tuple
from uuid import uuid4

from opwen_email_server import azure_constants as constants
from opwen_email_server import config
from opwen_email_server import events
from opwen_email_server.services.auth import AzureAuth
from opwen_email_server.services.queue import AzureQueue
from opwen_email_server.services.storage import AzureTextStorage
from opwen_email_server.utils.log import LogMixin

STORAGE = AzureTextStorage(account=config.BLOBS_ACCOUNT,
                           key=config.BLOBS_KEY,
                           container=constants.CONTAINER_SENDGRID_MIME,
                           provider=config.STORAGE_PROVIDER)

QUEUE = AzureQueue(namespace=config.QUEUES_NAMESPACE,
                   sas_key=config.QUEUES_SAS_KEY,
                   sas_name=config.QUEUES_SAS_NAME,
                   name=constants.QUEUE_SENDGRID_MIME)

CLIENTS = AzureAuth(account=config.TABLES_ACCOUNT,
                    key=config.TABLES_KEY,
                    table=constants.TABLE_AUTH,
                    provider=config.STORAGE_PROVIDER)


class _Receiver(LogMixin):
    def __call__(self, client_id: str, email: str) -> Tuple[str, int]:
        domain = CLIENTS.domain_for(client_id)
        if not domain:
            self.log_event(events.UNREGISTERED_CLIENT, {'client_id': client_id})  # noqa: E501
            return 'client is not registered', 403

        email_id = str(uuid4())

        STORAGE.store_text(email_id, email)

        QUEUE.enqueue({
            '_version': '0.1',
            '_type': 'mime_email_received',
            'resource_id': email_id,
            'container_name': STORAGE.container,
        })

        self.log_event(events.EMAIL_RECEIVED_FOR_CLIENT, {'domain': domain})  # noqa: E501
        return 'received', 200


receive = _Receiver()
