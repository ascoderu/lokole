from opwen_email_server.api import lokole_write
from opwen_email_server.api import sendgrid_sender
from opwen_email_server.services import client_datastore
from opwen_email_server.services import server_datastore
from opwen_email_server.utils.queue_consumer import QueueConsumer


class LokoleWriteQueueConsumer(QueueConsumer):
    def __init__(self):
        super().__init__(lokole_write.QUEUE.dequeue)

    def _process_message(self, message: dict):
        for email in client_datastore.unpack_emails(message['resource_id']):
            server_datastore.store_email(email['_uid'], email)

            sendgrid_sender.QUEUE.enqueue({
                '_version': '0.1',
                '_type': 'email_to_send',
                'resource_id': email['_uid'],
                'container_name': server_datastore.STORAGE.container,
            })


if __name__ == '__main__':
    consumer = LokoleWriteQueueConsumer()
    consumer.run_forever()
