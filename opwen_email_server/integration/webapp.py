from typing import Callable
from typing import Iterable
from typing import List
from typing import Optional
from typing import Union

from cached_property import cached_property
from flask_security import LoginForm
from libcloud.storage.types import ObjectDoesNotExistError

from opwen_email_client.domain.email.store import EmailStore
from opwen_email_client.domain.email.sync import Sync
from opwen_email_client.domain.email.user_store import User
from opwen_email_client.domain.email.user_store import UserReadStore
from opwen_email_client.domain.email.user_store import UserStore
from opwen_email_client.domain.email.user_store import UserWriteStore
from opwen_email_client.webapp.config import AppConfig
from opwen_email_server.constants import mailbox
from opwen_email_server.integration.azure import get_email_storage
from opwen_email_server.integration.azure import get_mailbox_storage
from opwen_email_server.integration.azure import get_pending_storage
from opwen_email_server.integration.azure import get_user_storage
from opwen_email_server.integration.celery import send_and_index_email
from opwen_email_server.services.storage import AzureObjectStorage
from opwen_email_server.services.storage import AzureTextStorage
from opwen_email_server.utils.collections import chunks
from opwen_email_server.utils.email_parser import descending_timestamp
from opwen_email_server.utils.email_parser import ensure_has_sent_at
from opwen_email_server.utils.email_parser import get_domain
from opwen_email_server.utils.email_parser import get_recipients
from opwen_email_server.utils.log import LogMixin


class AzureRole:
    def __init__(self):
        raise NotImplementedError


class AzureUser(User):
    def __init__(self, **data):
        super().__setattr__('_data', data)

    def __getattr__(self, item):
        data = super().__getattribute__('_data')
        return data.get(item)

    def __setattr__(self, key, value):
        data = super().__getattribute__('_data')
        data[key] = value

    @property
    def id(self) -> Union[str, int]:
        return self.email

    @property
    def email(self) -> str:
        return super().__getattribute__('_data')['email']

    @property
    def password(self) -> str:
        return super().__getattribute__('_data')['password']

    @property
    def roles(self) -> List[str]:
        return []

    @property
    def active(self) -> bool:
        return True

    @property
    def is_admin(self) -> bool:
        return False


class AzureUserStore(UserStore, UserReadStore, UserWriteStore):
    def __init__(self, user_storage: AzureObjectStorage):
        UserReadStore.__init__(self, user_model=AzureUser, role_model=AzureRole)
        UserWriteStore.__init__(self, db=None)
        UserStore.__init__(self, read=self, write=self)
        self._user_storage = user_storage

    def init_app(self, app):
        pass

    def fetch_all(self, user: AzureUser) -> List[AzureUser]:
        domain_users = []
        for email in self._user_storage.iter(f'{get_domain(user.email)}/'):
            domain_user = self.get_user(email)
            if domain_user is not None:
                domain_users.append(domain_user)
        return domain_users

    def fetch_pending(self) -> List[AzureUser]:
        return []

    def get_user(self, id_or_email) -> Optional[AzureUser]:
        try:
            data = self._user_storage.fetch_object(self._path_for(id_or_email))
        except ObjectDoesNotExistError:
            return None
        else:
            return AzureUser(**data)

    def find_user(self, *args, **kwargs) -> Optional[AzureUser]:
        if 'id' not in kwargs and 'email' not in kwargs:
            raise NotImplementedError(f'Unable to find_user by: {", ".join(kwargs.keys())}')

        id_or_email = kwargs.get('email') or kwargs.get('id')
        return self.get_user(id_or_email)

    def find_role(self, *args, **kwargs):
        raise NotImplementedError

    def put(self, user: AzureUser) -> AzureUser:
        return user

    def commit(self) -> None:
        pass

    def delete(self, user: AzureUser) -> None:
        self._user_storage.delete(self._path_for(user.email))

    @classmethod
    def _path_for(cls, email: str) -> str:
        return f'{get_domain(email)}/{email}'


class AzureEmailStore(EmailStore, LogMixin):
    def __init__(self, email_storage: AzureObjectStorage, mailbox_storage: AzureTextStorage,
                 pending_storage: AzureTextStorage, send_email: Callable[[str], None]):
        super().__init__(restricted=None)
        self._email_storage = email_storage
        self._mailbox_storage = mailbox_storage
        self._pending_storage = pending_storage
        self._send_email = send_email

    def _create(self, emails_or_attachments: Iterable[dict]):
        for email in emails_or_attachments:
            if email.get('_type') == 'attachment':
                raise NotImplementedError

            domain = get_domain(email.get('from', ''))
            if not domain.endswith(mailbox.MAILBOX_DOMAIN):
                continue

            ensure_has_sent_at(email)
            email.pop('csrf_token', None)
            email_id = email['_uid']
            self._email_storage.store_object(email_id, email)
            self._pending_storage.store_text(f'{domain}/{email_id}', 'pending')
            self._send_email(email_id)

    def get(self, uid: str) -> Optional[dict]:
        try:
            email = self._email_storage.fetch_object(uid)
        except ObjectDoesNotExistError:
            self.log_warning('Email at %s does not exist', uid)
            return None
        else:
            email['read'] = True
            for i, attachment in enumerate(email.get('attachments', [])):
                attachment.setdefault('_uid', i)
                attachment.setdefault('cid', None)
            return email

    def get_attachment(self, email_id: str, attachment_id: str) -> Optional[dict]:
        email = self.get(email_id)
        if not email:
            return None

        attachments = email.get('attachments', [])
        for attachment in attachments:
            if attachment.get('_uid') == attachment_id:
                return attachment

        try:
            return attachments[int(attachment_id)]
        except (IndexError, ValueError):
            return None

    def inbox(self, email_address: str, page: int) -> Iterable[dict]:
        return self._iter_mailbox(email_address, page, mailbox.RECEIVED_FOLDER)

    def sent(self, email_address: str, page: int) -> Iterable[dict]:
        return self._iter_mailbox(email_address, page, mailbox.SENT_FOLDER)

    def _iter_mailbox(self, email_address: str, page: int, folder: str) -> Iterable[dict]:
        domain = get_domain(email_address)
        emails = self._mailbox_storage.iter(f'{domain}/{email_address}/{folder}')
        for i, resource_ids in enumerate(chunks(emails, AppConfig.EMAILS_PER_PAGE), start=1):
            if i != page:
                continue
            for resource_id in resource_ids:
                email_id = resource_id.split('/')[-1]
                email = self.get(email_id)
                if email:
                    yield email

    def search(self, email_address: str, page: int, query: Optional[str]) -> Iterable[dict]:
        return []

    def outbox(self, email_address: str, page: int) -> Iterable[dict]:
        return []

    def pending(self, page: Optional[int]) -> Iterable[dict]:
        return []

    def has_unread(self, email_address: str) -> bool:
        return False

    def num_pending(self) -> int:
        return 0

    def _delete(self, email_address: str, uids: Iterable[str]):
        domain = get_domain(email_address)

        for uid in uids:
            email = self.get(uid)
            if not email:
                continue

            if email_address == email.get('from'):
                folder = mailbox.SENT_FOLDER
            elif email_address in get_recipients(email):
                folder = mailbox.RECEIVED_FOLDER
            else:
                continue

            desc_prefix = descending_timestamp(email['sent_at'])

            self._mailbox_storage.delete(f"{domain}/{email_address}/{folder}/{desc_prefix}/{uid}")

    def _mark_sent(self, uids: Iterable[str]):
        pass

    def _mark_read(self, email_address: str, uids: Iterable[str]):
        pass


class NoSync(Sync):
    def upload(self, items: Iterable, users: Iterable[User]) -> Iterable[str]:
        return []

    def download(self) -> Iterable:
        return []


class AzureIoc:
    @cached_property
    def email_store(self):
        return AzureEmailStore(
            email_storage=get_email_storage(),
            mailbox_storage=get_mailbox_storage(),
            pending_storage=get_pending_storage(),
            send_email=send_and_index_email,
        )

    @cached_property
    def email_sync(self):
        return NoSync()

    @cached_property
    def user_store(self):
        return AzureUserStore(user_storage=get_user_storage())

    @cached_property
    def login_form(self):
        return LoginForm
