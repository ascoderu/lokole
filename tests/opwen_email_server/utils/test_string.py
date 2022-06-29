from unittest import TestCase

from opwen_email_server.utils.string import is_lowercase
from opwen_email_server.utils.string import urlsafe


class IsLowercaseTests(TestCase):

    def test_lowercase(self):
        self.assertTrue(is_lowercase('foo'))

    def test_uppercase(self):
        self.assertFalse(is_lowercase('FoO'))


class UrlsafeTests(TestCase):

    def test_url_characters(self):
        self.assertEqual(urlsafe('foo/bar=baz'), 'foo%2Fbar%3Dbaz')
