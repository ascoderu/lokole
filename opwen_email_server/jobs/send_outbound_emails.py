from opwen_email_server.backend import email_sender
from opwen_email_server.backend import server_datastore
from opwen_email_server.services.queue_consumer import QueueConsumer


class OutboundEmailQueueConsumer(QueueConsumer):
    def __init__(self):
        super().__init__(email_sender.QUEUE.dequeue)

    def _process_message(self, message: dict):
        resource_id = message['resource_id']
        email = server_datastore.fetch_email(resource_id)
        self.log_info('Fetched outbound email %s for sending', resource_id)

        email_sender.send(email)
        self.log_info('Done sending outbound email %s', resource_id)


if __name__ == '__main__':
    from opwen_email_server.jobs.job import main
    main(OutboundEmailQueueConsumer)
