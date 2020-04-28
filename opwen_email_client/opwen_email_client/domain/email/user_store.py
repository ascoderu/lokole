from abc import ABCMeta
from abc import abstractmethod
from typing import List
from typing import Union

from flask import Flask
from flask_login import UserMixin
from flask_security.datastore import Datastore as UserWriteStore
from flask_security.datastore import UserDatastore as UserReadStore


class User(UserMixin):
    @property
    @abstractmethod
    def id(self) -> Union[str, int]:
        raise NotImplementedError  # pragma: no cover

    @property
    @abstractmethod
    def email(self) -> str:
        raise NotImplementedError  # pragma: no cover

    @property
    @abstractmethod
    def password(self) -> str:
        raise NotImplementedError  # pragma: no cover

    @property
    @abstractmethod
    def roles(self) -> List[str]:
        raise NotImplementedError  # pragma: no cover

    @property
    @abstractmethod
    def active(self) -> bool:
        raise NotImplementedError  # pragma: no cover


class UserStore(metaclass=ABCMeta):
    def __init__(self, read: UserReadStore, write: UserWriteStore) -> None:
        self.r = read
        self.w = write

    def init_app(self, app: Flask) -> None:
        pass

    @abstractmethod
    def fetch_all(self, user: User) -> List[User]:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def fetch_pending(self) -> List[User]:
        raise NotImplementedError  # pragma: no cover
