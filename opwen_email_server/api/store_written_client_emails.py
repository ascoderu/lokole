from opwen_email_server.backend import client_datastore
from opwen_email_server.backend import email_sender
from opwen_email_server.backend import server_datastore
from opwen_email_server.utils.log import LogMixin


class _WrittenStorer(LogMixin):
    def __call__(self, resource_id: str):
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

        client_datastore.delete(resource_id)
        self.log_info('Deleted packaged client emails from %s', resource_id)

        return 'OK', 200


store = _WrittenStorer()
