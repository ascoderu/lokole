from unittest import TestCase

import zlib

from utils.serialization import CompressedJson


class TestCompressedJson(TestCase):
    def test_serializer_handles_non_compressed_data(self):
        serializer = CompressedJson()
        deserialized = serializer.deserialize(b'{"not":"compressed"}')
        self.assertEqual(None, deserialized)

    def test_serializer_handles_non_json_data(self):
        serializer = CompressedJson()
        deserialized = serializer.deserialize(zlib.compress(b'not-json'))
        self.assertEqual(None, deserialized)

    def test_serializer_roundtrip(self):
        serializer = CompressedJson()
        for expected in {'a': 1}, [2, 'b'], 'three', 4:
            actual = serializer.deserialize(serializer.serialize(expected))
            self.assertEqual(expected, actual)
