from abc import ABCMeta
from abc import abstractmethod
from base64 import b64decode
from base64 import b64encode


class AttachmentEncoder(metaclass=ABCMeta):
    @abstractmethod
    def encode(self, content: bytes) -> str:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def decode(self, encoded: str) -> bytes:
        raise NotImplementedError  # pragma: no cover


class Base64AttachmentEncoder(AttachmentEncoder):
    encoding = 'utf-8'

    def encode(self, content):
        content_bytes = b64encode(content)
        return content_bytes.decode(self.encoding)

    def decode(self, encoded):
        content_bytes = encoded.encode(self.encoding)
        return b64decode(content_bytes)
