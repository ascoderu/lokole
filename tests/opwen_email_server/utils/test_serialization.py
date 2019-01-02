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


class ToJsonlBytesTests(TestCase):
    def test_creates_jsonl_bytes(self):
        serialized = serialization.to_jsonl_bytes({'a': 1, 'b': '你好'})

        self.assertTrue(serialized.endswith(b'\n'))
        self.assertNotIn(b' ', serialized)


class FromJsonlBytesTests(TestCase):
    def test_parses_jsonl_lines(self):
        lines = [
            b'{"a":1}\n',
            b'{"b":2}\n'
        ]

        deserialized = [serialization.from_jsonl_bytes(line) for line in lines]

        self.assertEqual([{"a": 1}, {"b": 2}], deserialized)

    def test_parses_json_lines(self):
        lines = [
            b'[\n',
            b'{"a":1},\n',
            b'{"b":2}\n',
            b']',
        ]

        deserialized = [serialization.from_jsonl_bytes(line) for line in lines]

        self.assertEqual([None, {"a": 1}, {"b": 2}, None], deserialized)


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
