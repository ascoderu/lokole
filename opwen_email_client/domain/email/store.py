from abc import ABCMeta
from abc import abstractmethod
from typing import Iterable
from typing import Optional
from typing import Union
from uuid import uuid4


class EmailStore(metaclass=ABCMeta):
    def create(self, emails: Iterable[dict]):
        self._create(map(_add_uid, emails))

    @abstractmethod
    def _create(self, emails: Iterable[dict]):
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get(self, uid: str) -> Optional[dict]:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def inbox(self, email_address: str) -> Iterable[dict]:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def outbox(self, email_address: str) -> Iterable[dict]:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def sent(self, email_address: str) -> Iterable[dict]:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def search(self, email_address: str,
               query: Optional[str]) -> Iterable[dict]:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def pending(self) -> Iterable[dict]:
        raise NotImplementedError  # pragma: no cover

    def mark_sent(self, emails_or_uids: Iterable[Union[dict, str]]):
        uids = map(_get_uid, emails_or_uids)
        return self._mark_sent(uids)

    def mark_read(self, email_address: str,
                  emails_or_uids: Iterable[Union[dict, str]]):
        uids = map(_get_uid, emails_or_uids)
        return self._mark_read(email_address, uids)

    def delete(self, email_address: str,
               emails_or_uids: Iterable[Union[dict, str]]):
        uids = map(_get_uid, emails_or_uids)
        return self._delete(email_address, uids)

    @abstractmethod
    def _delete(self, email_address: str, uids: Iterable[str]):
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def _mark_sent(self, uids: Iterable[str]):
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def _mark_read(self, email_address: str, uids: Iterable[str]):
        raise NotImplementedError  # pragma: no cover


def _get_uid(email_or_uid: Union[str, dict]) -> str:
    try:
        return email_or_uid['_uid']
    except TypeError:
        return email_or_uid


def _add_uid(email: dict) -> dict:
    email.setdefault('_uid', str(uuid4()))
    return email
