from collections import namedtuple

from babel import Locale
from flask import request
from flask import session

from opwen_email_client.config import AppConfig


# noinspection PyClassHasNoInit
class FileInfo(namedtuple('FileInfo', 'name content')):
    pass


class AttachmentsStore(object):
    def __init__(self, attachment_encoder, email_store):
        """
        :type attachment_encoder: opwen_domain.email.AttachmentEncoder
        :type email_store: opwen_domain.email.EmailStore

        """
        self._attachment_encoder = attachment_encoder
        self._email_store = email_store

    @property
    def _session_store(self):
        """
        :rtype: dict

        """
        session_attachments = session.get('attachments')
        if not session_attachments:
            session_attachments = session['attachments'] = {}

        return session_attachments

    def store(self, emails):
        """
        :type emails: collections.Iterable[dict]

        """
        for i, email in enumerate(emails):
            email_id = email['_uid']
            attachments = email.get('attachments', [])
            for j, attachment in enumerate(attachments):
                attachment_filename = attachment.get('filename', '')
                attachment_id = '{}-{}'.format(i + 1, attachment_filename)
                attachment['id'] = attachment_id
                self._session_store[attachment_id] = (email_id, j)

    def lookup(self, attachment_id):
        """
        :type attachment_id: str
        :rtype: opwen_email_client.session.FileInfo | None

        """
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

        attachment = attachments[attachment_idx]
        filename = attachment.get('filename')
        content = attachment.get('content')
        if not filename or not content:
            return None

        return FileInfo(name=filename, content=self._attachment_encoder.decode(content))


class Session(object):
    _current_locale_key = 'current_locale'
    _last_visited_url_key = 'last_visited_url'

    @classmethod
    def _session(cls):
        """
        :rtype: dict[str, str]

        """
        return session or {}

    @classmethod
    def store_last_visited_url(cls):
        if request.endpoint not in ('favicon', 'static'):
            cls._session()[cls._last_visited_url_key] = request.url

    @classmethod
    def get_last_visited_url(cls):
        """
        :rtype: str | None

        """
        return cls._session().get(cls._last_visited_url_key)

    @classmethod
    def store_current_locale(cls, locale):
        """
        :type locale: str

        """
        cls._session()[cls._current_locale_key] = locale

    @classmethod
    def get_current_locale(cls):
        """
        :rtype: babel.Locale

        """
        locale = cls._session().get(cls._current_locale_key)
        return Locale.parse(locale) if locale else AppConfig.DEFAULT_LOCALE
