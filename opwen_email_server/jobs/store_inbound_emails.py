from typing import Tuple

from opwen_email_server.api import email_receive
from opwen_email_server.services import server_datastore
from opwen_email_server.utils.email_parser import parse_mime_email
from opwen_email_server.utils.queue_consumer import QueueConsumer


class InboundEmailQueueConsumer(QueueConsumer):
    def __init__(self):
        super().__init__(email_receive.QUEUE.dequeue)

    def _process_message(self, message: dict):
        email_id, mime_email = self._load_email_content(message)
        email = parse_mime_email(mime_email)
        email['_delivered'] = False
        server_datastore.store_email(email_id, email)

    @classmethod
    def _load_email_content(cls, message: dict) -> Tuple[str, str]:
        email_id = message['resource_id']
        mime_email = email_receive.STORAGE.fetch_text(email_id)
        return email_id, mime_email


if __name__ == '__main__':
    consumer = InboundEmailQueueConsumer()
    consumer.run_forever()
