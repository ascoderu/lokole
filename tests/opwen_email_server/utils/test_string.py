from unittest import TestCase

from opwen_email_server.utils.string import is_lowercase


class IsLowercaseTests(TestCase):
    def test_lowercase(self):
        self.assertTrue(is_lowercase('foo'))

    def test_uppercase(self):
        self.assertFalse(is_lowercase('FoO'))
