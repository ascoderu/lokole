from opwen_email_server.api import email_send
from opwen_email_server.services import server_datastore
from opwen_email_server.utils.queue_consumer import QueueConsumer


class OutboundEmailQueueConsumer(QueueConsumer):
    def __init__(self):
        super().__init__(email_send.QUEUE.dequeue)

    def _process_message(self, message: dict):
        email = server_datastore.fetch_email(message['resource_id'])
        email_send.send(email)


if __name__ == '__main__':
    consumer = OutboundEmailQueueConsumer()
    consumer.run_forever()
