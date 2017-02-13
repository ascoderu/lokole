from base64 import b64decode
from base64 import b64encode


class Base64AttachmentEncoder(object):
    encoding = 'utf-8'

    def encode(self, content):
        """
        :type content: bytes
        :rtype: str

        """
        content_bytes = b64encode(content)
        return content_bytes.decode(self.encoding)

    def decode(self, encoded):
        """
        :type encoded: str
        :rtype: bytes

        """
        content_bytes = encoded.encode(self.encoding)
        return b64decode(content_bytes)
