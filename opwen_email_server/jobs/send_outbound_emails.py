from opwen_email_server.backend import email_sender
from opwen_email_server.backend import server_datastore
from opwen_email_server.services.queue_consumer import QueueConsumer


class OutboundEmailQueueConsumer(QueueConsumer):
    def __init__(self):
        super().__init__(email_sender.QUEUE.dequeue)

    def _process_message(self, message: dict):
        email = server_datastore.fetch_email(message['resource_id'])
        email_sender.send(email)
        self.log_debug('done sending email %s', email.get('_uid'))


if __name__ == '__main__':
    consumer = OutboundEmailQueueConsumer()
    consumer.run_forever()
