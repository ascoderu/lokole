from typing import Tuple

from opwen_email_server import azure_constants as constants
from opwen_email_server import config
from opwen_email_server import events
from opwen_email_server.services.auth import AzureAuth
from opwen_email_server.services.storage import AzureTextStorage
from opwen_email_server.utils.log import LogMixin

import celery
from opwen_email_server.api.store_written_client_emails import store

CLIENTS = AzureAuth(
    storage=AzureTextStorage(
        account=config.TABLES_ACCOUNT,
        key=config.TABLES_KEY,
        container=constants.TABLE_AUTH,
        provider=config.STORAGE_PROVIDER))


class _Uploader(LogMixin):
    def __call__(self, client_id: str, upload_info: dict) -> Tuple[str, int]:
        domain = CLIENTS.domain_for(client_id)
        if not domain:
            self.log_event(events.UNREGISTERED_CLIENT, {'client_id': client_id})  # noqa: E501
            return 'client is not registered', 403

        resource_type = upload_info.get('resource_type')
        resource_id = upload_info.get('resource_id')
        resource_container = upload_info.get('resource_container')

        result = store.delay(resource_id)

        self.log_event(events.EMAILS_RECEIVED_FROM_CLIENT, {'domain': domain})  # noqa: E501
        return 'uploaded', 200


upload = _Uploader()
