from abc import ABC
from hashlib import sha256
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import Tuple
from typing import Union

from libcloud.storage.types import ObjectDoesNotExistError

from opwen_email_server.constants import events
from opwen_email_server.constants import mailbox
from opwen_email_server.constants import sync
from opwen_email_server.services.auth import Auth
from opwen_email_server.services.sendgrid import SendSendgridEmail
from opwen_email_server.services.storage import AzureObjectsStorage
from opwen_email_server.services.storage import AzureObjectStorage
from opwen_email_server.services.storage import AzureTextStorage
from opwen_email_server.utils.email_parser import MimeEmailParser
from opwen_email_server.utils.email_parser import descending_timestamp
from opwen_email_server.utils.email_parser import ensure_has_sent_at
from opwen_email_server.utils.email_parser import get_domain
from opwen_email_server.utils.email_parser import get_domains
from opwen_email_server.utils.email_parser import get_recipients
from opwen_email_server.utils.log import LogMixin
from opwen_email_server.utils.serialization import from_base64
from opwen_email_server.utils.serialization import from_jsonl_bytes
from opwen_email_server.utils.serialization import to_base64
from opwen_email_server.utils.serialization import to_jsonl_bytes
from opwen_email_server.utils.string import is_lowercase
from opwen_email_server.utils.unique import new_email_id

Response = Union[dict, Tuple[str, int]]


class _Action(ABC, LogMixin):
    def __call__(self, *args, **kwargs) -> Response:
        try:
            return self._action(*args, **kwargs)
        except Exception as ex:
            self.log_exception(ex, '%s(args=%r, kwargs=%r)', self.__class__.__name__, args, kwargs)
            raise ex

    def _action(self, *args, **kwargs) -> Response:
        raise NotImplementedError  # pragma: no cover


class Ping(_Action):
    # noinspection PyMethodMayBeStatic
    def _action(self):  # type: ignore
        return 'OK', 200


class SendOutboundEmails(_Action):
    def __init__(self, email_storage: AzureObjectStorage, send_email: SendSendgridEmail):

        self._email_storage = email_storage
        self._send_email = send_email

    def _action(self, resource_id):  # type: ignore
        email = self._email_storage.fetch_object(resource_id)

        success = self._send_email(email)
        if not success:
            return 'error', 500

        self.log_event(events.EMAIL_DELIVERED_FROM_CLIENT, {'domain': get_domain(email.get('from', ''))})  # noqa: E501  # yapf: disable
        return 'OK', 200


class StoreInboundEmails(_Action):
    def __init__(self,
                 raw_email_storage: AzureTextStorage,
                 email_storage: AzureObjectStorage,
                 pending_storage: AzureTextStorage,
                 next_task: Callable[[str], None],
                 email_parser: Callable[[str], dict] = None):

        self._raw_email_storage = raw_email_storage
        self._email_storage = email_storage
        self._pending_storage = pending_storage
        self._next_task = next_task
        self._email_parser = email_parser or MimeEmailParser()

    def _action(self, resource_id):  # type: ignore
        try:
            mime_email = self._raw_email_storage.fetch_text(resource_id)
        except ObjectDoesNotExistError:
            self.log_warning('Inbound email %s does not exist', resource_id)
            return 'skipped', 202

        email = self._email_parser(mime_email)
        email_id = self._store_inbound_email(email)

        self._raw_email_storage.delete(resource_id)
        self._next_task(email_id)

        self.log_event(events.EMAIL_STORED_FOR_CLIENT, {'domain': get_domain(email.get('from') or '')})  # noqa: E501  # yapf: disable
        return 'OK', 200

    def _store_inbound_email(self, email: dict) -> str:
        ensure_has_sent_at(email)
        email_id = new_email_id(email)
        email['_uid'] = email_id

        self._email_storage.store_object(email_id, email)

        for domain in get_domains(email):
            if domain.endswith(mailbox.MAILBOX_DOMAIN):
                self._pending_storage.store_text(f'{domain}/{email_id}', 'pending')

        return email_id


class _IndexEmailForMailbox(_Action):
    def __init__(self, email_storage: AzureObjectStorage, mailbox_storage: AzureTextStorage):
        self._email_storage = email_storage
        self._mailbox_storage = mailbox_storage

    def _action(self, resource_id):  # type: ignore
        email = self._email_storage.fetch_object(resource_id)

        for email_address in self._get_pivot(email):
            domain = get_domain(email_address)
            desc_prefix = descending_timestamp(email['sent_at'])
            if domain.endswith(mailbox.MAILBOX_DOMAIN):
                index = f"{domain}/{email_address}/{self._folder}/{desc_prefix}/{resource_id}"
                self._mailbox_storage.store_text(index, 'indexed')

        self.log_event(events.MAILBOX_EMAIL_INDEXED, {'folder': self._folder})  # noqa: E501  # yapf: disable
        return 'OK', 200

    @property
    def _folder(self) -> str:
        raise NotImplementedError  # pragma: no cover

    def _get_pivot(self, email: dict) -> Iterable[str]:
        raise NotImplementedError  # pragma: no cover


class IndexReceivedEmailForMailbox(_IndexEmailForMailbox):
    _folder = mailbox.RECEIVED_FOLDER

    def _get_pivot(self, email: dict) -> Iterable[str]:
        for email_address in get_recipients(email):
            yield email_address


class IndexSentEmailForMailbox(_IndexEmailForMailbox):
    _folder = mailbox.SENT_FOLDER

    def _get_pivot(self, email: dict) -> Iterable[str]:
        sender = email.get('from')
        if sender:
            yield sender


class StoreWrittenClientEmails(_Action):
    def __init__(self, client_storage: AzureObjectsStorage, email_storage: AzureObjectStorage,
                 user_storage: AzureObjectStorage, next_task: Callable[[str], None]):

        self._client_storage = client_storage
        self._email_storage = email_storage
        self._user_storage = user_storage
        self._next_task = next_task

    def _action(self, resource_id):  # type: ignore
        self._store_emails(resource_id)
        self._store_users(resource_id)
        self._client_storage.delete(resource_id)

        return 'OK', 200

    def _store_emails(self, resource_id):
        emails = self._client_storage.fetch_objects(resource_id, (sync.EMAILS_FILE, from_jsonl_bytes))

        domain = ''
        num_stored = 0
        for email in emails:
            email_id = email['_uid']
            email = self._decode_attachments(email)
            self._email_storage.store_object(email_id, email)

            self._next_task(email_id)

            num_stored += 1
            domain = get_domain(email.get('from', ''))

        self.log_event(events.EMAIL_STORED_FROM_CLIENT, {'domain': domain, 'num_emails': num_stored})  # noqa: E501  # yapf: disable

    def _store_users(self, resource_id):
        users = self._client_storage.fetch_objects(resource_id, (sync.USERS_FILE, from_jsonl_bytes))

        domain = ''
        num_stored = 0
        for user in users:
            email = user['email']
            domain = get_domain(email)
            self._user_storage.store_object(f'{domain}/{email}', user)

            num_stored += 1

        self.log_event(events.USER_STORED_FROM_CLIENT, {'domain': domain, 'num_users': num_stored})  # noqa: E501  # yapf: disable

    @classmethod
    def _decode_attachments(cls, email: dict) -> dict:
        if not email.get('attachments'):
            return email

        for attachment in email['attachments']:
            attachment['content'] = from_base64(attachment['content'])

        return email


class ReceiveInboundEmail(_Action):
    def __init__(self, auth: Auth, raw_email_storage: AzureTextStorage, next_task: Callable[[str], None]):
        self._auth = auth
        self._raw_email_storage = raw_email_storage
        self._next_task = next_task

    def _action(self, client_id=None, email=None, **sendgrid_args):  # type: ignore
        if email is None:
            return 'email cannot be None', 400

        domain = self._auth.domain_for(client_id)
        if not domain:
            self.log_event(events.UNREGISTERED_CLIENT, {'client_id': client_id})  # noqa: E501  # yapf: disable
            return 'client is not registered', 403

        email_id = self._new_email_id(email)

        self._raw_email_storage.store_text(email_id, email)

        self._next_task(email_id)

        self.log_event(events.EMAIL_RECEIVED_FOR_CLIENT, {'domain': domain})  # noqa: E501  # yapf: disable
        return 'received', 200

    @classmethod
    def _new_email_id(cls, email: str) -> str:
        return sha256(email.encode('utf-8')).hexdigest()


class ProcessServiceEmail(_Action):
    def __init__(self,
                 raw_email_storage: AzureTextStorage,
                 email_storage: AzureObjectStorage,
                 next_task: Callable[[str], None],
                 registry: Dict[str, Any],
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

        for address in email.get('to', []):
            try:
                mailer_service = self._registry[address]
            except KeyError:
                self.log_warning('Skipping unknown mailer service: %s', address)
                continue

            formatted_email = mailer_service(email)

            formatted_email_id = new_email_id(formatted_email)
            formatted_email['_uid'] = formatted_email_id

            self._email_storage.store_object(formatted_email_id, formatted_email)

            self._next_task(formatted_email_id)

        self._raw_email_storage.delete(resource_id)
        self.log_event(events.EMAILS_FORMATTED_FOR_CLIENT)  # noqa: E501  # yapf: disable
        return 'OK', 200


class DownloadClientEmails(_Action):
    def __init__(self, auth: Auth, client_storage: AzureObjectsStorage, email_storage: AzureObjectStorage,
                 pending_storage: AzureTextStorage):

        self._auth = auth
        self._client_storage = client_storage
        self._email_storage = email_storage
        self._pending_storage = pending_storage

    def _action(self, client_id, compression):  # type: ignore
        domain = self._auth.domain_for(client_id)
        if not domain:
            self.log_event(events.UNREGISTERED_CLIENT, {'client_id': client_id})  # noqa: E501  # yapf: disable
            return 'client is not registered', 403

        if compression not in self._client_storage.compression_formats():
            self.log_event(events.UNKNOWN_COMPRESSION_FORMAT, {'client_id': client_id})  # noqa: E501  # yapf: disable
            return f'unknown compression format "{compression}"', 400

        delivered = set()

        def mark_delivered(email: dict) -> dict:
            delivered.add(email['_uid'])
            return email

        pending = self._fetch_pending_emails(domain)
        pending = (mark_delivered(email) for email in pending)
        pending = (self._encode_attachments(email) for email in pending)

        resource_id = self._client_storage.store_objects((sync.EMAILS_FILE, pending, to_jsonl_bytes), compression)

        self._mark_emails_as_delivered(domain, delivered)

        self.log_event(events.EMAILS_DELIVERED_TO_CLIENT, {'domain': domain, 'num_emails': len(delivered)})  # noqa: E501  # yapf: disable
        return {
            'resource_id': resource_id,
        }

    def _fetch_pending_emails(self, domain: str) -> Iterable[dict]:
        for email_id in self._pending_storage.iter(f'{domain}/'):
            yield self._email_storage.fetch_object(email_id)

    @classmethod
    def _encode_attachments(cls, email: dict) -> dict:
        if not email.get('attachments'):
            return email

        for attachment in email['attachments']:
            content_bytes = attachment['content']
            attachment['content'] = to_base64(content_bytes)

        return email

    def _mark_emails_as_delivered(self, domain: str, email_ids: Iterable[str]) -> None:
        for email_id in email_ids:
            self._pending_storage.delete(f'{domain}/{email_id}')


class UploadClientEmails(_Action):
    def __init__(self, auth: Auth, next_task: Callable[[str], None]):
        self._auth = auth
        self._next_task = next_task

    def _action(self, client_id, upload_info):  # type: ignore
        domain = self._auth.domain_for(client_id)
        if not domain:
            self.log_event(events.UNREGISTERED_CLIENT, {'client_id': client_id})  # noqa: E501  # yapf: disable
            return 'client is not registered', 403

        resource_id = upload_info['resource_id']

        self._next_task(resource_id)

        self.log_event(events.EMAILS_RECEIVED_FROM_CLIENT, {'domain': domain})  # noqa: E501  # yapf: disable
        return 'uploaded', 200


class RegisterClient(_Action):
    def __init__(self, auth: Auth, client_storage: AzureObjectsStorage, setup_mailbox: Callable[[str, str], None],
                 setup_mx_records: Callable[[str], None], client_id_source: Callable[[], str]):
        self._auth = auth
        self._client_storage = client_storage
        self._setup_mailbox = setup_mailbox
        self._setup_mx_records = setup_mx_records
        self._client_id_source = client_id_source

    def _action(self, domain, owner):  # type: ignore
        client_id = self._client_id_source()

        self._setup_mailbox(client_id, domain)
        self._setup_mx_records(domain)
        self._client_storage.ensure_exists()
        self._auth.insert(client_id, domain, owner)

        self.log_event(events.NEW_CLIENT_REGISTERED, {'domain': domain})  # noqa: E501  # yapf: disable
        return 'OK', 200


class CreateClient(_Action):
    def __init__(self, auth: Auth, task: Callable[[str, str], None]):
        self._auth = auth
        self._task = task

    def _action(self, client, user, **auth_args):  # type: ignore
        domain = client['domain']
        if not is_lowercase(domain):
            return 'domain must be lowercase', 400
        if self._auth.client_id_for(domain) is not None:
            return 'client already exists', 409

        self._task(domain, user)

        self.log_event(events.CLIENT_CREATED, {'domain': domain})  # noqa: E501  # yapf: disable
        return 'accepted', 201


class ListClients(_Action):
    def __init__(self, auth: Auth):
        self._auth = auth

    def _action(self, **auth_args):  # type: ignore
        clients = [{'domain': domain} for domain in self._auth.domains()]

        self.log_event(events.CLIENTS_FETCHED)  # noqa: E501  # yapf: disable
        return {
            'clients': clients,
        }


class GetClient(_Action):
    def __init__(self, auth: Auth, client_storage: AzureObjectsStorage):
        self._auth = auth
        self._client_storage = client_storage

    def _action(self, domain, user, **auth_args):  # type: ignore
        if not is_lowercase(domain):
            return 'domain must be lowercase', 400

        client_id = self._auth.client_id_for(domain)
        if client_id is None:
            return 'client does not exist', 404

        if not self._auth.is_owner(domain, user):
            return 'client does not belong to the user', 403

        access_info = self._client_storage.access_info()

        self.log_event(events.CLIENT_FETCHED, {'domain': domain})  # noqa: E501  # yapf: disable
        return {
            'client_id': client_id,
            'storage_account': access_info.account,
            'storage_key': access_info.key,
            'resource_container': access_info.container,
        }


class DeleteClient(_Action):
    def __init__(self, auth: Auth, delete_mailbox: Callable[[str, str], None], delete_mx_records: Callable[[str], None],
                 mailbox_storage: AzureTextStorage, pending_storage: AzureTextStorage,
                 user_storage: AzureObjectStorage):
        self._auth = auth
        self._delete_mailbox = delete_mailbox
        self._delete_mx_records = delete_mx_records
        self._mailbox_storage = mailbox_storage
        self._pending_storage = pending_storage
        self._user_storage = user_storage

    def _action(self, domain, user, **auth_args):  # type: ignore
        if not is_lowercase(domain):
            return 'domain must be lowercase', 400

        client_id = self._auth.client_id_for(domain)
        if client_id is None:
            return 'client does not exist', 404

        if not self._auth.is_owner(domain, user):
            return 'client does not belong to the user', 403

        self._delete_mailbox(client_id, domain)
        self._delete_mx_records(domain)
        self._delete_index(self._pending_storage, domain)
        self._delete_index(self._mailbox_storage, domain)
        self._delete_index(self._user_storage, domain)
        self._auth.delete(client_id, domain)

        self.log_event(events.CLIENT_DELETED, {'domain': domain})  # noqa: E501  # yapf: disable
        return 'OK', 200

    @classmethod
    def _delete_index(cls, storage: Union[AzureTextStorage, AzureObjectStorage], domain: str) -> None:
        for prefix in storage.iter(f'{domain}/'):
            storage.delete(f'{domain}/{prefix}')


class CalculateNumberOfUsersMetric(_Action):
    def __init__(self, auth: Auth, user_storage: AzureObjectStorage):
        self._auth = auth
        self._user_storage = user_storage

    def _action(self, domain, user, **auth_args):  # type: ignore
        if not self._auth.is_owner(domain, user):
            return 'client does not belong to the user', 403

        users = sum(1 for _ in self._user_storage.iter(f'{domain}/'))

        return {
            'users': users,
        }


class CalculatePendingEmailsMetric(_Action):
    def __init__(self, auth: Auth, pending_storage: AzureTextStorage):
        self._auth = auth
        self._pending_storage = pending_storage

    def _action(self, domain, user, **auth_args):  # type: ignore
        if not self._auth.is_owner(domain, user):
            return 'client does not belong to the user', 403

        pending_emails = sum(1 for _ in self._pending_storage.iter(f'{domain}/'))

        return {
            'pending_emails': pending_emails,
        }
