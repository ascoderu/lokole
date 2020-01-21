from cached_property import cached_property

from flask_security import LoginForm
from libcloud.storage.types import ObjectDoesNotExistError
from opwen_email_client.domain.email.user_store import User
from opwen_email_client.domain.email.user_store import UserReadStore
from opwen_email_client.domain.email.user_store import UserStore
from opwen_email_client.domain.email.user_store import UserWriteStore
from opwen_email_client.webapp.ioc import Ioc

from opwen_email_server.integration.azure import get_user_storage
from opwen_email_server.services.storage import AzureObjectStorage
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

    def fetch_all(self, user):
        for email in self._user_storage.iter(f'{get_domain(user.email)}/'):
            user = self.get_user(email)
            if user is not None:
                yield user

    def fetch_pending(self):
        return []

    def get_user(self, id_or_email):
        try:
            data = self._user_storage.fetch_object(self._path_for(id_or_email))
        except ObjectDoesNotExistError:
            return None
        else:
            return AzureUser(**data)

    def find_user(self, *args, **kwargs):
        if 'id' not in kwargs and 'email' not in kwargs:
            raise NotImplementedError(f'Unable to find_user by: {", ".join(kwargs.keys())}')

        id_or_email = kwargs.get('email') or kwargs.get('id')
        return self.get_user(id_or_email)

    def find_role(self, *args, **kwargs):
        raise NotImplementedError  # pragma: nocover

    def put(self, user):
        self._pending_users[user.email] = user
        return user

    def commit(self):
        for user in self._pending_users.values():
            data = user.to_dict()

            # FIXME: deal with datetime serialization
            data.pop('last_login_at', None)
            data.pop('current_login_at', None)

            self._user_storage.store_object(self._path_for(user.email), data)

    def delete(self, user):
        self._pending_users.pop(user.email, None)
        self._user_storage.delete(self._path_for(user.email))

    @classmethod
    def _path_for(cls, email):
        return f'{get_domain(email)}/{email}'


class AzureIoc(Ioc):
    @cached_property
    def user_store(self):
        return AzureUserStore(user_storage=get_user_storage())

    @cached_property
    def login_form(self):
        return LoginForm
