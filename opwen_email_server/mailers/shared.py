from typing import Callable
from typing import Dict

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
                 registry: Dict[str, Callable[[dict], dict]],
                 email_parser: Callable[[dict], dict] = None):

        self._raw_email_storage = raw_email_storage
        self._email_storage = email_storage
        self._next_task = next_task
        self._registry = registry
        self._email_parser = email_parser or MimeEmailParser()

    def _action(self, resource_id):  # type: ignore
        try:
            mime_email = self._raw_email_storage.fetch_text(resource_id)
        except ObjectDoesNotExistError:
            self.log_warning('Inbound email %s does not exist', resource_id)
            return 'skipped', 202

        email = self._email_parser(mime_email)

        for address in email['to']:
            mailer_service = self._registry[address]
            formatted_email = mailer_service(email)

            email_id = new_email_id(formatted_email)
            formatted_email['_uid'] = email_id

            self._email_storage.store_email(formatted_email, email_id)

            self._next_task(email_id)

        self._raw_email_storage.delete(resource_id)
