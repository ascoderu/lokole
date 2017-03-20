from typing import Any
from typing import Callable
from typing import Tuple

from opwen_email_server.api import sendgrid
from opwen_email_server.services import datastore
from opwen_email_server.services.queue import AzureQueue
from opwen_email_server.services.storage import AzureStorage
from opwen_email_server.utils.email_parser import parse_mime_email
from opwen_email_server.utils.queue_consumer import QueueConsumer


class SendgridQueueConsumer(QueueConsumer):
    def __init__(self, queue: AzureQueue, storage: AzureStorage,
                 store_email: Callable[[str, dict], Any]) -> None:

        super().__init__(queue.dequeue)
        self._storage = storage
        self._store_email = store_email

    def _process_message(self, message: dict):
        email_id, mime_email = self._load_email_content(message)
        email = parse_mime_email(mime_email)
        email['_delivered'] = False
        self._store_email(email_id, email)

    def _load_email_content(self, message: dict) -> Tuple[str, str]:
        email_id = message['resource_id']
        mime_email = self._storage.fetch_text(email_id)
        return email_id, mime_email


if __name__ == '__main__':
    consumer = SendgridQueueConsumer(sendgrid.QUEUE,
                                     sendgrid.STORAGE,
                                     datastore.store_email)
    consumer.run_forever()
