from unittest import TestCase

from utils.serialization import CompressedJson


class TestCompressedJson(TestCase):
    def test_serializer_is_null_safe(self):
        serializer = CompressedJson()
        self.assertEqual(b'', serializer.serialize(None))
        self.assertEqual(u'', serializer.deserialize(None))

    def test_serializer_roundtrip(self):
        serializer = CompressedJson()
        for expected in {'a': 1}, [2, 'b'], 'three', 4:
            actual = serializer.deserialize(serializer.serialize(expected))
            self.assertEqual(expected, actual)
