from opwen_email_server import azure_constants as constants
from opwen_email_server import config
from opwen_email_server import events
from opwen_email_server.backend import server_datastore
from opwen_email_server.services.queue import AzureQueue
from opwen_email_server.services.storage import AzureObjectStorage
from opwen_email_server.utils.email_parser import get_domain
from opwen_email_server.utils.log import LogMixin

QUEUE = AzureQueue(namespace=config.QUEUES_NAMESPACE,
                   sas_key=config.QUEUES_SAS_KEY,
                   sas_name=config.QUEUES_SAS_NAME,
                   name=constants.QUEUE_EMAIL_SEND)

STORAGE = AzureObjectStorage(account=config.CLIENT_STORAGE_ACCOUNT,
                             key=config.CLIENT_STORAGE_KEY,
                             container=constants.CONTAINER_CLIENT_PACKAGES,
                             provider=config.STORAGE_PROVIDER)


class _WrittenStorer(LogMixin):
    def __call__(self, resource_id: str):
        emails = STORAGE.fetch_objects(resource_id)

        domain = ''
        num_stored = 0
        for email in emails:
            email_id = email['_uid']
            server_datastore.store_outbound_email(email_id, email)

            # noinspection PyProtectedMember
            container = server_datastore._get_email_storage().container

            QUEUE.enqueue({
                '_version': '0.1',
                '_type': 'email_to_send',
                'resource_id': email_id,
                'container_name': container,
            })
            num_stored += 1
            domain = get_domain(email.get('from', ''))

        STORAGE.delete(resource_id)

        self.log_event(events.EMAIL_STORED_FROM_CLIENT, {'domain': domain, 'num_emails': num_stored})  # noqa: E501
        return 'OK', 200


store = _WrittenStorer()
