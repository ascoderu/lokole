from unittest import TestCase

from opwen_email_server.utils import collections


class ToIterableTests(TestCase):
    def test_makes_item_iterable(self):
        obj = {'a': 1, 'b': 2}

        collection = collections.to_iterable(obj)

        self.assertSequenceEqual(list(collection), [obj])

    def test_ignores_none(self):
        obj = None

        collection = collections.to_iterable(obj)

        self.assertSequenceEqual(list(collection), [])


class ChunksTests(TestCase):
    def test_creates_fullsize_chunks(self):
        chunks = collections.chunks([1, 2, 3, 4], 2)

        self.assertEqual(list(chunks), [(1, 2), (3, 4)])

    def test_creates_nonfull_chunks(self):
        chunks = collections.chunks([1, 2, 3, 4], 3)

        self.assertEqual(list(chunks), [(1, 2, 3), (4, )])
