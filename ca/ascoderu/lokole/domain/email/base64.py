from base64 import b64decode
from base64 import b64encode

from ca.ascoderu.lokole.domain.email.interfaces import AttachmentEncoder


class Base64AttachmentEncoder(AttachmentEncoder):
    encoding = 'utf-8'

    def encode(self, content):
        content_bytes = b64encode(content)
        return content_bytes.decode(self.encoding)

    def decode(self, encoded):
        content_bytes = encoded.encode(self.encoding)
        return b64decode(content_bytes)
