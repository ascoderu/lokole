from unittest import TestCase

from opwen_email_server.utils import serialization


class JsonTests(TestCase):
    def test_creates_slim_json(self):
        serialized = serialization.to_json({'a': 1, 'b': 2})

        self.assertNotIn('\n', serialized)
        self.assertNotIn(' ', serialized)

    def test_roundtrip(self):
        obj = {'a': 1, 'b': [2]}

        self.assertEqual(obj, serialization.from_json(serialization.to_json(obj)))


class Base64Tests(TestCase):
    def test_roundtrip(self):
        original = b'some bytes'
        serialized = serialization.to_base64(original)
        deserialized = serialization.from_base64(serialized)

        self.assertEqual(original, deserialized)


class MsgpackTests(TestCase):
    def test_roundtrip(self):
        original = {'a': 1, 'b': '你好'}
        serialized = serialization.to_msgpack_bytes(original)
        deserialized = serialization.from_msgpack_bytes(serialized)

        self.assertEqual(original, deserialized)


class JsonlTests(TestCase):
    def test_roundtrip(self):
        original = {'a': 1, 'b': '你好'}
        serialized = serialization.to_jsonl_bytes(original)
        deserialized = serialization.from_jsonl_bytes(serialized)

        self.assertEqual(original, deserialized)

    def test_parses_jsonl_lines(self):
        lines = [b'{"a":1}\n', b'{"b":2}\n']

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

    def test_handles_non_utf8(self):
        deserialized = serialization.from_jsonl_bytes(b'\xff\xfef\x00o\x00o\x00')

        self.assertIsNone(deserialized)


class GzipTests(TestCase):
    sample_string = b'hello world\n'

    sample_compressed = (b'\x1f\x8b\x08\x08;\n\xfdX\x00\x03foo.txt\x00\xcbH\xcd\xc9\xc9W('
                         b'\xcf/\xcaI\xe1\x02\x00-;\x08\xaf\x0c\x00\x00\x00')

    def test_roundtrip(self):
        compressed = serialization.gzip_bytes(self.sample_string)
        decompressed = serialization.gunzip_bytes(compressed)

        self.assertEqual(self.sample_string, decompressed)

    def test_gunzip(self):
        decompressed = serialization.gunzip_bytes(self.sample_compressed)

        self.assertEqual(decompressed, self.sample_string)
