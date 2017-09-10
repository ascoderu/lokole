from collections import namedtuple
from functools import wraps
from typing import Dict
from typing import Iterable
from typing import Optional

from flask import request
from flask import session

from opwen_email_client.domain.email.attachment import AttachmentEncoder
from opwen_email_client.domain.email.store import EmailStore


# noinspection PyClassHasNoInit
class FileInfo(namedtuple('FileInfo', 'name content')):
    pass


class AttachmentsStore(object):
    def __init__(self, attachment_encoder: AttachmentEncoder,
                 email_store: EmailStore):
        self._attachment_encoder = attachment_encoder
        self._email_store = email_store

    @property
    def _session_store(self) -> dict:
        session_attachments = session.get('attachments')
        if not session_attachments:
            session_attachments = session['attachments'] = {}

        return session_attachments

    def store(self, emails: Iterable[dict]):
        for i, email in enumerate(emails):
            email_id = email['_uid']
            attachments = email.get('attachments', [])
            for j, attachment in enumerate(attachments):
                attachment_filename = attachment.get('filename', '')
                attachment_id = '{}-{}'.format(i + 1, attachment_filename)
                attachment['id'] = attachment_id
                self._session_store[attachment_id] = (email_id, j)

    def lookup(self, attachment_id: str) -> Optional[FileInfo]:
        try:
            email_id, attachment_idx = self._session_store[attachment_id]
        except KeyError:
            return None

        email = self._email_store.get(email_id)
        if email is None:
            return None

        attachments = email.get('attachments', [])
        if attachment_idx >= len(attachments):
            return None

        attachment = attachments[attachment_idx]  # type: Dict
        filename = attachment.get('filename')
        content = attachment.get('content')
        if not filename or not content:
            return None

        return FileInfo(filename, self._attachment_encoder.decode(content))


class Session(object):
    _current_language_key = 'current_language'
    _last_visited_url_key = 'last_visited_url'

    @classmethod
    def _session(cls) -> Dict[str, str]:
        return session

    @classmethod
    def store_last_visited_url(cls):
        cls._session()[cls._last_visited_url_key] = request.url

    @classmethod
    def get_last_visited_url(cls) -> Optional[str]:
        return cls._session().get(cls._last_visited_url_key)

    @classmethod
    def store_current_language(cls, language: str):
        cls._session()[cls._current_language_key] = language

    @classmethod
    def get_current_language(cls) -> str:
        return cls._session().get(cls._current_language_key)


def track_history(func):
    @wraps(func)
    def history_tracker(*args, **kwargs):
        Session.store_last_visited_url()
        return func(*args, **kwargs)

    return history_tracker
