from abc import ABCMeta
from abc import abstractmethod
from typing import Dict
from typing import Iterable
from typing import Optional
from typing import Set
from typing import Union
from uuid import uuid4


class EmailStore(metaclass=ABCMeta):
    def __init__(self, restricted: Optional[Dict[str, Set[str]]] = None):
        self._restricted = restricted or {}

    def create(self, emails_or_attachments: Iterable[dict]):
        self._create((
            _add_uid(email_or_attachment)
            for email_or_attachment in emails_or_attachments
            if not _is_restricted(email_or_attachment, self._restricted)
        ))

    @abstractmethod
    def _create(self, emails_or_attachments: Iterable[dict]):
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get(self, uid: str) -> Optional[dict]:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get_attachment(self, uid: str) -> Optional[dict]:
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

    @abstractmethod
    def num_pending(self) -> int:
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


def _is_restricted(email: dict, restricted: Dict[str, Set[str]]) -> bool:
    type_ = email.get('_type')
    if type_ and type_ != 'email':
        return False

    sender = email.get('from', '')
    recipients = _get_recipients(email)

    return any(restricted_inbox in recipients and sender not in allowed_senders
               for restricted_inbox, allowed_senders in restricted.items())


def _get_uid(email_or_uid: Union[str, dict]) -> str:
    try:
        return email_or_uid['_uid']
    except TypeError:
        return email_or_uid


def _get_recipients(email: dict) -> Set[str]:
    recipients = set()
    recipients.update(email.get('to', []))
    recipients.update(email.get('cc', []))
    recipients.update(email.get('bcc', []))
    return recipients


def _add_uid(email: dict) -> dict:
    email.setdefault('_uid', str(uuid4()))
    for attachment in email.get('attachments', []):
        attachment.setdefault('_uid', str(uuid4()))
    return email
