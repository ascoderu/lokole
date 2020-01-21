from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import Union

from cached_property import cached_property
from flask_security import LoginForm
from libcloud.storage.types import ObjectDoesNotExistError
from opwen_email_client.domain.email.store import EmailStore
from opwen_email_client.domain.email.user_store import User
from opwen_email_client.domain.email.user_store import UserReadStore
from opwen_email_client.domain.email.user_store import UserStore
from opwen_email_client.domain.email.user_store import UserWriteStore
from opwen_email_client.util.serialization import JsonSerializer
from opwen_email_client.webapp.config import AppConfig

from opwen_email_server.constants import mailbox
from opwen_email_server.integration.azure import get_email_storage
from opwen_email_server.integration.azure import get_mailbox_storage
from opwen_email_server.integration.azure import get_user_storage
from opwen_email_server.services.storage import AzureObjectStorage
from opwen_email_server.utils.collections import chunks
from opwen_email_server.utils.email_parser import get_domain


class AzureRole:
    def __init__(self):
        raise NotImplementedError  # pragma: no cover


class AzureUser(User):
    def __init__(self, **data):
        super().__setattr__('_data', data)

    def __getattr__(self, item):
        data = super().__getattribute__('_data')
        return data.get(item)

    def __setattr__(self, key, value):
        data = super().__getattribute__('_data')
        data[key] = value

    def to_dict(self):
        data = super().__getattribute__('_data')
        return data

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


class AzureUserStore(UserStore, UserReadStore, UserWriteStore):
    def __init__(self, user_storage: AzureObjectStorage):
        UserReadStore.__init__(self, user_model=AzureUser, role_model=AzureRole)
        UserWriteStore.__init__(self, db=None)
        UserStore.__init__(self, read=self, write=self)
        self._pending_users = {}
        self._user_storage = user_storage

    def init_app(self, app):
        pass

    def fetch_all(self, user: User) -> List[User]:
        for email in self._user_storage.iter(f'{get_domain(user.email)}/'):
            user = self.get_user(email)
            if user is not None:
                yield user

    def fetch_pending(self) -> List[User]:
        return []

    def get_user(self, id_or_email) -> Optional[User]:
        try:
            data = self._user_storage.fetch_object(self._path_for(id_or_email))
        except ObjectDoesNotExistError:
            return None
        else:
            return AzureUser(**data)

    def find_user(self, *args, **kwargs) -> Optional[User]:
        if 'id' not in kwargs and 'email' not in kwargs:
            raise NotImplementedError(f'Unable to find_user by: {", ".join(kwargs.keys())}')

        id_or_email = kwargs.get('email') or kwargs.get('id')
        return self.get_user(id_or_email)

    def find_role(self, *args, **kwargs):
        raise NotImplementedError  # pragma: nocover

    def put(self, user: User) -> User:
        self._pending_users[user.email] = user
        return user

    def commit(self) -> None:
        for user in self._pending_users.values():
            data = user.to_dict()

            # FIXME: deal with datetime serialization
            data.pop('last_login_at', None)
            data.pop('current_login_at', None)

            self._user_storage.store_object(self._path_for(user.email), data)

    def delete(self, user: User) -> None:
        self._pending_users.pop(user.email, None)
        self._user_storage.delete(self._path_for(user.email))

    @classmethod
    def _path_for(cls, email: str) -> str:
        return f'{get_domain(email)}/{email}'


class AzureEmailStore(EmailStore):
    def __init__(self,
                 email_storage: AzureObjectStorage,
                 mailbox_storage: AzureObjectStorage,
                 restricted: Optional[Dict[str, Set[str]]] = None):
        super().__init__(restricted)
        self._email_storage = email_storage
        self._mailbox_storage = mailbox_storage

    def _create(self, emails_or_attachments: Iterable[dict]):
        raise NotImplementedError

    def get(self, uid: str) -> Optional[dict]:
        try:
            email = self._email_storage.fetch_object(uid)
        except ObjectDoesNotExistError:
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
        emails = self._mailbox_storage.iter(f'{email_address}/{folder}')
        for i, resource_ids in enumerate(chunks(emails, AppConfig.EMAILS_PER_PAGE), start=1):
            if i != page:
                continue
            for resource_id in resource_ids:
                email_id = resource_id.split('/')[-1]
                yield self.get(email_id)

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
        pass

    def _mark_sent(self, uids: Iterable[str]):
        pass

    def _mark_read(self, email_address: str, uids: Iterable[str]):
        pass


class AzureIoc:
    @cached_property
    def serializer(self):
        return JsonSerializer()

    @cached_property
    def email_server_client(self):
        raise NotImplementedError

    @cached_property
    def email_store(self):
        return AzureEmailStore(
            email_storage=get_email_storage(),
            mailbox_storage=get_mailbox_storage(),
        )

    @cached_property
    def email_sync(self):
        raise NotImplementedError

    @cached_property
    def user_store(self):
        return AzureUserStore(user_storage=get_user_storage())

    @cached_property
    def login_form(self):
        return LoginForm
