from abc import ABCMeta
from abc import abstractmethod
from typing import List

from flask import Flask
from flask_login import UserMixin
from flask_security.datastore import Datastore as _UserWriteStore
from flask_security.datastore import UserDatastore as _UserReadStore


class UserStore(metaclass=ABCMeta):
    def __init__(self, read: _UserReadStore, write: _UserWriteStore) -> None:
        self.r = read
        self.w = write

    def init_app(self, app: Flask) -> None:
        pass

    @abstractmethod
    def fetch_all(self) -> List[UserMixin]:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def fetch_pending(self) -> List[UserMixin]:
        raise NotImplementedError  # pragma: no cover
