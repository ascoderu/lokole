from opwen_email_server.api import email_receive
from opwen_email_server.backend import server_datastore
from opwen_email_server.utils.email_parser import inline_images
from opwen_email_server.utils.email_parser import parse_mime_email
from opwen_email_server.utils.log import LogMixin


class _InboundStorer(LogMixin):
    def __call__(self, resource_id: str):
        mime_email = email_receive.STORAGE.fetch_text(resource_id)
        self.log_info('Fetched inbound MIME email %s', resource_id)

        email = parse_mime_email(mime_email)
        email = inline_images(email)
        server_datastore.store_email(resource_id, email)
        self.log_info('Stored inbound email %s', resource_id)

        email_receive.STORAGE.delete(resource_id)
        self.log_info('Deleted inbound MIME email %s', resource_id)

        return 'OK', 200


store = _InboundStorer()
