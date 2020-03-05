from typing import Callable

from libcloud.storage.types import ObjectDoesNotExistError

from opwen_email_server.actions import _Action
from opwen_email_server.services.storage import AzureObjectStorage
from opwen_email_server.services.storage import AzureTextStorage
from opwen_email_server.utils.email_parser import MimeEmailParser
from opwen_email_server.utils.unique import new_email_id


class ProcessServiceEmail(_Action):
    def __init__(self,
                 raw_email_storage: AzureTextStorage,
                 email_storage: AzureObjectStorage,
                 next_task: Callable[[str], None],
                 email_formatter: Callable[[str], dict] = None,
                 email_parser: Callable[[dict], dict] = None):

        self._raw_email_storage = raw_email_storage
        self._next_task = next_task
        self._email_formatter = email_formatter
        self._email_parser = email_parser or MimeEmailParser()

    def _action(self, resource_id):  # type: ignore
        try:
            mime_email = self._raw_email_storage.fetch_text(resource_id)
        except ObjectDoesNotExistError:
            self.log_warning('Inbound email %s does not exist', resource_id)
            return 'skipped', 202

        email = self._email_parser(mime_email)

        formatted_email = self._email_formatter(email)
        email_id = new_email_id(formatted_email)
        formatted_email['_uid'] = email_id

        self.email_storage.store_email(formatted_email, email_id)
        self._raw_email_storage.delete(resource_id)

        self._next_task(email_id)
