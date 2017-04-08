from opwen_email_server.api import client_write
from opwen_email_server.backend import client_datastore
from opwen_email_server.backend import email_send
from opwen_email_server.backend import server_datastore
from opwen_email_server.services.queue_consumer import QueueConsumer


class ClientWriteQueueConsumer(QueueConsumer):
    def __init__(self):
        super().__init__(client_write.QUEUE.dequeue)

    def _process_message(self, message: dict):
        for email in client_datastore.unpack_emails(message['resource_id']):
            server_datastore.store_email(email['_uid'], email)

            email_send.QUEUE.enqueue({
                '_version': '0.1',
                '_type': 'email_to_send',
                'resource_id': email['_uid'],
                'container_name': server_datastore.STORAGE.container,
            })


if __name__ == '__main__':
    consumer = ClientWriteQueueConsumer()
    consumer.run_forever()
