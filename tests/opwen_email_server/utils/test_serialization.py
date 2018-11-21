from unittest import TestCase

from opwen_email_server.utils import serialization


class ToJsonTests(TestCase):
    def test_creates_slim_json(self):
        serialized = serialization.to_json({'a': 1, 'b': 2})

        self.assertNotIn('\n', serialized)
        self.assertNotIn(' ', serialized)


class FromJsonTests(TestCase):
    def test_roundtrip(self):
        obj = {'a': 1, 'b': [2]}

        self.assertEqual(obj, serialization.from_json(
            serialization.to_json(obj)))


class GzipTests(TestCase):
    sample_string = 'hello world\n'

    sample_compressed = (
        b'\x1f\x8b\x08\x08;\n\xfdX\x00\x03foo.txt\x00\xcbH\xcd\xc9\xc9W('
        b'\xcf/\xcaI\xe1\x02\x00-;\x08\xaf\x0c\x00\x00\x00')

    def test_roundtrip(self):
        compressed = serialization.gzip_string(self.sample_string)
        print(compressed)
        decompressed = serialization.gunzip_string(compressed)

        self.assertEqual(self.sample_string, decompressed)

    def test_gunzip(self):
        decompressed = serialization.gunzip_string(self.sample_compressed)

        self.assertEqual(decompressed, self.sample_string)
