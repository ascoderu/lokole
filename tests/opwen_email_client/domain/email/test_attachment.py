from unittest import TestCase

from opwen_email_client.domain.email.attachment import Base64AttachmentEncoder


class AttachmentEncoderTests(TestCase):
    @property
    def encodable_objects(self):
        """
        :rtype: collections.Iterable

        """
        yield b'some bytes'
        yield u'some unicode bytes: \u2603'.encode('utf-8')

    def setUp(self):
        self.encoder = Base64AttachmentEncoder()

    def test_encoding_roundtrip(self):
        for original in self.encodable_objects:
            encoded = self.encoder.encode(original)
            decoded = self.encoder.decode(encoded)
            self.assertEqual(original, decoded)
