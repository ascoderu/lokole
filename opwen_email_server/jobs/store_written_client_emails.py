from opwen_email_server.api import client_write
from opwen_email_server.backend import client_datastore
from opwen_email_server.backend import email_sender
from opwen_email_server.backend import server_datastore
from opwen_email_server.services.queue_consumer import QueueConsumer


class ClientWriteQueueConsumer(QueueConsumer):
    def __init__(self):
        super().__init__(client_write.QUEUE.dequeue)

    def _process_message(self, message: dict):
        resource_id = message['resource_id']
        emails = client_datastore.unpack_emails(resource_id)
        self.log_info('Fetched packaged client emails from %s', resource_id)

        for email in emails:
            email_id = email['_uid']
            server_datastore.store_email(email_id, email)
            self.log_info('Stored packaged client email %s', email_id)

            email_sender.QUEUE.enqueue({
                '_version': '0.1',
                '_type': 'email_to_send',
                'resource_id': email_id,
                'container_name': server_datastore.STORAGE.container,
            })
            self.log_info('Ingesting packaged client email %s', email_id)


if __name__ == '__main__':
    from opwen_email_server.jobs.job import main
    main(ClientWriteQueueConsumer)
