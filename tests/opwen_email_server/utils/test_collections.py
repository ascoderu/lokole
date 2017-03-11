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
