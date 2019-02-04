from abc import ABC
from typing import Callable
from typing import Iterable
from typing import Tuple
from typing import Union
from uuid import uuid4

from opwen_email_server.constants import events
from opwen_email_server.constants import sync
from opwen_email_server.services.auth import AzureAuth
from opwen_email_server.services.sendgrid import SendSendgridEmail
from opwen_email_server.services.storage import AzureObjectStorage
from opwen_email_server.services.storage import AzureObjectsStorage
from opwen_email_server.services.storage import AzureTextStorage
from opwen_email_server.utils.email_parser import format_attachments
from opwen_email_server.utils.email_parser import format_inline_images
from opwen_email_server.utils.email_parser import get_domain
from opwen_email_server.utils.email_parser import get_domains
from opwen_email_server.utils.email_parser import parse_mime_email
from opwen_email_server.utils.log import LogMixin
from opwen_email_server.utils.serialization import from_base64
from opwen_email_server.utils.serialization import from_jsonl_bytes
from opwen_email_server.utils.serialization import to_base64
from opwen_email_server.utils.serialization import to_jsonl_bytes
from opwen_email_server.utils.string import is_lowercase

Response = Union[dict, Tuple[str, int]]


class _Action(ABC, LogMixin):
    def __call__(self, *args, **kwargs) -> Response:
        try:
            return self._action(*args, **kwargs)
        except Exception as ex:
            self.log_exception(ex, 'error in action %s',
                               self.__class__.__name__)
            raise ex

    def _action(self, *args, **kwargs) -> Response:
        raise NotImplementedError


class Ping(_Action):
    # noinspection PyMethodMayBeStatic
    def _action(self):  # type: ignore
        return 'OK', 200


class SendOutboundEmails(_Action):
    def __init__(self,
                 email_storage: AzureObjectStorage,
                 send_email: SendSendgridEmail):

        self._email_storage = email_storage
        self._send_email = send_email

    def _action(self, resource_id):  # type: ignore
        email = self._email_storage.fetch_object(resource_id)

        success = self._send_email(email)
        if not success:
            return 'error', 500

        self.log_event(events.EMAIL_DELIVERED_FROM_CLIENT, {'domain': get_domain(email.get('from', ''))})  # noqa: E501
        return 'OK', 200


class StoreInboundEmails(_Action):
    def __init__(self,
                 raw_email_storage: AzureTextStorage,
                 email_storage: AzureObjectStorage,
                 pending_factory: Callable[[str], AzureTextStorage],
                 email_parser: Callable[[str], dict] = None):

        self._raw_email_storage = raw_email_storage
        self._email_storage = email_storage
        self._pending_factory = pending_factory
        self._email_parser = email_parser or self._parse_mime_email

    def _action(self, resource_id):  # type: ignore
        mime_email = self._raw_email_storage.fetch_text(resource_id)

        email = self._email_parser(mime_email)
        self._store_inbound_email(resource_id, email)

        self._raw_email_storage.delete(resource_id)

        self.log_event(events.EMAIL_STORED_FOR_CLIENT, {'domain': get_domain(email.get('from') or '')})  # noqa: E501
        return 'OK', 200

    def _store_inbound_email(self, email_id: str, email: dict):
        email['_uid'] = email_id

        self._email_storage.store_object(email_id, email)

        for domain in get_domains(email):
            pending_storage = self._pending_factory(domain)
            pending_storage.store_text(email_id, 'pending')

    @classmethod
    def _parse_mime_email(cls, mime_email: str) -> dict:
        email = parse_mime_email(mime_email)
        email = format_attachments(email)
        email = format_inline_images(email)
        return email


class StoreWrittenClientEmails(_Action):
    def __init__(self,
                 client_storage: AzureObjectsStorage,
                 email_storage: AzureObjectStorage,
                 next_task: Callable[[str], None]):

        self._client_storage = client_storage
        self._email_storage = email_storage
        self._next_task = next_task

    def _action(self, resource_id):  # type: ignore
        emails = self._client_storage.fetch_objects(
            resource_id, (sync.EMAILS_FILE, from_jsonl_bytes))

        domain = ''
        num_stored = 0
        for email in emails:
            email_id = email['_uid']
            email = self._decode_attachments(email)
            self._email_storage.store_object(email_id, email)

            self._next_task(email_id)

            num_stored += 1
            domain = get_domain(email.get('from', ''))

        self._client_storage.delete(resource_id)

        self.log_event(events.EMAIL_STORED_FROM_CLIENT, {'domain': domain, 'num_emails': num_stored})  # noqa: E501
        return 'OK', 200

    @classmethod
    def _decode_attachments(cls, email: dict) -> dict:
        if not email.get('attachments'):
            return email

        for attachment in email['attachments']:
            attachment['content'] = from_base64(attachment['content'])

        return email


class ReceiveInboundEmail(_Action):
    def __init__(self,
                 auth: AzureAuth,
                 raw_email_storage: AzureTextStorage,
                 next_task: Callable[[str], None],
                 email_id_source: Callable[[], str] = None):

        self._auth = auth
        self._raw_email_storage = raw_email_storage
        self._next_task = next_task
        self._email_id_source = email_id_source or self._new_email_id

    def _action(self, client_id, email):  # type: ignore
        domain = self._auth.domain_for(client_id)
        if not domain:
            self.log_event(events.UNREGISTERED_CLIENT, {'client_id': client_id})  # noqa: E501
            return 'client is not registered', 403

        email_id = self._email_id_source()

        self._raw_email_storage.store_text(email_id, email)

        self._next_task(email_id)

        self.log_event(events.EMAIL_RECEIVED_FOR_CLIENT, {'domain': domain})  # noqa: E501
        return 'received', 200

    @classmethod
    def _new_email_id(cls) -> str:
        return str(uuid4())


class DownloadClientEmails(_Action):
    def __init__(self,
                 auth: AzureAuth,
                 client_storage: AzureObjectsStorage,
                 email_storage: AzureObjectStorage,
                 pending_factory: Callable[[str], AzureTextStorage]):

        self._auth = auth
        self._client_storage = client_storage
        self._email_storage = email_storage
        self._pending_factory = pending_factory

    def _action(self, client_id, compression):  # type: ignore
        domain = self._auth.domain_for(client_id)
        if not domain:
            self.log_event(events.UNREGISTERED_CLIENT, {'client_id': client_id})  # noqa: E501
            return 'client is not registered', 403

        if compression not in self._client_storage.compression_formats():
            self.log_event(events.UNKNOWN_COMPRESSION_FORMAT, {'client_id': client_id})  # noqa: E501
            return 'unknown compression format "{}"'.format(compression), 400

        delivered = set()

        def mark_delivered(email: dict) -> dict:
            delivered.add(email['_uid'])
            return email

        pending_storage = self._pending_factory(domain)

        pending = self._fetch_pending_emails(pending_storage)
        pending = (mark_delivered(email) for email in pending)
        pending = (self._encode_attachments(email) for email in pending)

        resource_id = self._client_storage.store_objects(
            (sync.EMAILS_FILE, pending, to_jsonl_bytes),
            compression)

        self._mark_emails_as_delivered(pending_storage, delivered)

        self.log_event(events.EMAILS_DELIVERED_TO_CLIENT, {'domain': domain, 'num_emails': len(delivered)})  # noqa: E501
        return {
            'resource_id': resource_id,
        }

    def _fetch_pending_emails(self, pending_storage: AzureTextStorage):
        for email_id in pending_storage.iter():
            yield self._email_storage.fetch_object(email_id)

    @classmethod
    def _encode_attachments(cls, email: dict) -> dict:
        if not email.get('attachments'):
            return email

        for attachment in email['attachments']:
            content_bytes = attachment['content']
            attachment['content'] = to_base64(content_bytes)

        return email

    @classmethod
    def _mark_emails_as_delivered(cls, pending_storage: AzureTextStorage,
                                  email_ids: Iterable[str]):
        for email_id in email_ids:
            pending_storage.delete(email_id)


class UploadClientEmails(_Action):
    def __init__(self,
                 auth: AzureAuth,
                 next_task: Callable[[str], None]):

        self._auth = auth
        self._next_task = next_task

    def _action(self, client_id, upload_info):  # type: ignore
        domain = self._auth.domain_for(client_id)
        if not domain:
            self.log_event(events.UNREGISTERED_CLIENT, {'client_id': client_id})  # noqa: E501
            return 'client is not registered', 403

        resource_id = upload_info['resource_id']

        self._next_task(resource_id)

        self.log_event(events.EMAILS_RECEIVED_FROM_CLIENT, {'domain': domain})  # noqa: E501
        return 'uploaded', 200


class RegisterClient(_Action):
    def __init__(self,
                 auth: AzureAuth,
                 client_storage: AzureObjectsStorage,
                 setup_mailbox: Callable[[str, str], None],
                 setup_mx_records: Callable[[str], None],
                 client_id_source: Callable[[], str] = None):

        self._auth = auth
        self._client_storage = client_storage
        self._setup_mailbox = setup_mailbox
        self._setup_mx_records = setup_mx_records
        self._client_id_source = client_id_source or self._new_client_id

    def _action(self, client):  # type: ignore
        domain = client['domain']
        if not is_lowercase(domain):
            return 'domain must be lowercase', 400
        if self._auth.client_id_for(domain) is not None:
            return 'client already exists', 409

        client_id = self._client_id_source()
        access_info = self._client_storage.access_info()

        self._setup_mailbox(client_id, domain)
        self._setup_mx_records(domain)
        self._client_storage.ensure_exists()
        self._auth.insert(client_id, domain)

        self.log_event(events.NEW_CLIENT_REGISTERED, {'domain': domain})  # noqa: E501
        return {
            'client_id': client_id,
            'storage_account': access_info.account,
            'storage_key': access_info.key,
            'resource_container': access_info.container,
        }

    @classmethod
    def _new_client_id(cls) -> str:
        return str(uuid4())
