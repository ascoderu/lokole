from collections import Counter
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


class SingletonTests(TestCase):

    def test_creates_object_only_once(self):
        value1 = self.function1()
        value2 = self.function1()
        value3 = self.function2()
        value4 = self.function2()

        self.assertIs(value1, value2)
        self.assertIs(value3, value4)
        self.assertIsNot(value1, value3)
        self.assertEqual(self.call_counts['function1'], 1)
        self.assertEqual(self.call_counts['function2'], 1)

    def setUp(self):
        self.call_counts = Counter()

    @collections.singleton
    def function1(self):
        self.call_counts['function1'] += 1
        return 'some-value'

    @collections.singleton
    def function2(self):
        self.call_counts['function2'] += 1
        return 'some-other-value'


class AppendTests(TestCase):

    def test_yields_item_after_items(self):
        collection = collections.append([1, 2, 3], 4)

        self.assertSequenceEqual(list(collection), [1, 2, 3, 4])
