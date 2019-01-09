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
    def serialize(self, obj: T) -> bytes:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def deserialize(self, serialized: bytes) -> T:
        raise NotImplementedError  # pragma: no cover


class JsonSerializer(Serializer):
    _encoding = 'utf-8'
    _separators = (',', ':')

    def serialize(self, email: dict) -> bytes:
        email = self._encode_attachments(email)
        serialized = dumps(email, separators=self._separators)
        return serialized.encode(self._encoding)

    def deserialize(self, serialized: bytes) -> dict:
        decoded = serialized.decode(self._encoding)
        email = loads(decoded)
        email = self._decode_attachments(email)
        return email

    @classmethod
    def _encode_attachments(cls, email: dict) -> dict:
        attachments = email.get('attachments', [])
        if not attachments:
            return email

        email = deepcopy(email)
        for attachment in email['attachments']:
            content = attachment.get('content', b'')
            if content:
                attachment['content'] = b64encode(content).decode('ascii')
        return email

    @classmethod
    def _decode_attachments(cls, email: dict) -> dict:
        attachments = email.get('attachments', [])
        if not attachments:
            return email

        email = deepcopy(email)
        for attachment in email['attachments']:
            content = attachment.get('content', '')
            if content:
                attachment['content'] = b64decode(content)
        return email
