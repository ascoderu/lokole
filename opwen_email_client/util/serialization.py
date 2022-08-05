from abc import ABCMeta
from abc import abstractmethod
from base64 import b64decode
from base64 import b64encode
from copy import deepcopy
from json import dumps
from json import loads
from typing import TypeVar

T = TypeVar('T')


class Serializer(metaclass=ABCMeta):
    @abstractmethod
    def serialize(self, obj: T, type_: str = '') -> bytes:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def deserialize(self, serialized: bytes, type_: str = '') -> T:
        raise NotImplementedError  # pragma: no cover


class JsonSerializer(Serializer):
    _encoding = 'utf-8'
    _separators = (',', ':')

    def serialize(self, obj: dict, type_: str = '') -> bytes:
        if not type_ or type_ == 'email':
            obj = self._encode_attachments(obj)
        elif type_ == 'attachment':
            self._encode_attachment(obj)

        serialized = dumps(obj, separators=self._separators, sort_keys=True)
        return serialized.encode(self._encoding)

    def deserialize(self, serialized: bytes, type_: str = '') -> dict:
        decoded = serialized.decode(self._encoding)
        obj = loads(decoded)

        if not type_ or type_ == 'email':
            email = obj
            email = self._decode_attachments(email)
            return email
        elif type_ == 'attachment':
            attachment = obj
            self._decode_attachment(attachment)
            return attachment

    @classmethod
    def _encode_attachments(cls, email: dict) -> dict:
        attachments = email.get('attachments', [])
        if not attachments:
            return email

        email = deepcopy(email)
        for attachment in email['attachments']:
            cls._encode_attachment(attachment)
        return email

    @classmethod
    def _encode_attachment(cls, attachment: dict) -> None:
        content = attachment.get('content', b'')
        if content:
            attachment['content'] = b64encode(content).decode('ascii')

    @classmethod
    def _decode_attachments(cls, email: dict) -> dict:
        attachments = email.get('attachments', [])
        if not attachments:
            return email

        email = deepcopy(email)
        for attachment in email['attachments']:
            cls._decode_attachment(attachment)
        return email

    @classmethod
    def _decode_attachment(cls, attachment: dict) -> None:
        content = attachment.get('content', '')
        if content:
            attachment['content'] = b64decode(content)
