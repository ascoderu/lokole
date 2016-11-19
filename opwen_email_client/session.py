from collections import namedtuple

from flask import session


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
