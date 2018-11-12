from opwen_email_server import events
from opwen_email_server.backend import server_datastore
from opwen_email_server.backend.services import CLIENT_STORAGE as STORAGE
from opwen_email_server.services import tasks
from opwen_email_server.utils.email_parser import get_domain
from opwen_email_server.utils.log import LogMixin


class _WrittenStorer(LogMixin):
    def __call__(self, resource_id: str):
        emails = STORAGE.fetch_objects(resource_id)

        domain = ''
        num_stored = 0
        for email in emails:
            email_id = email['_uid']
            server_datastore.store_outbound_email(email_id, email)

            tasks.send.delay(email_id)

            num_stored += 1
            domain = get_domain(email.get('from', ''))

        STORAGE.delete(resource_id)

        self.log_event(events.EMAIL_STORED_FROM_CLIENT, {'domain': domain, 'num_emails': num_stored})  # noqa: E501
        return 'OK', 200


store = _WrittenStorer()
