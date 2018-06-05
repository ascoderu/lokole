from opwen_email_server.backend import email_sender
from opwen_email_server.backend import server_datastore
from opwen_email_server.utils.log import LogMixin


class _Sender(LogMixin):
    def __call__(self, message: dict):
        resource_id = message.get('resource_id', '')
        email = server_datastore.fetch_email(resource_id)
        self.log_info('Fetched outbound email %s for sending', resource_id)

        email_sender.send(email)
        self.log_info('Done sending outbound email %s', resource_id)

        return 'OK', 200


send = _Sender()
