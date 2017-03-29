from typing import Tuple

from opwen_email_server.api import sendgrid_receiver
from opwen_email_server.services import server_datastore
from opwen_email_server.utils.email_parser import parse_mime_email
from opwen_email_server.utils.queue_consumer import QueueConsumer


class SendgridQueueConsumer(QueueConsumer):
    def __init__(self):
        super().__init__(sendgrid_receiver.QUEUE.dequeue)

    def _process_message(self, message: dict):
        email_id, mime_email = self._load_email_content(message)
        email = parse_mime_email(mime_email)
        email['_delivered'] = False
        server_datastore.store_email(email_id, email)

    @classmethod
    def _load_email_content(cls, message: dict) -> Tuple[str, str]:
        email_id = message['resource_id']
        mime_email = sendgrid_receiver.STORAGE.fetch_text(email_id)
        return email_id, mime_email


if __name__ == '__main__':
    consumer = SendgridQueueConsumer()
    consumer.run_forever()
