from unittest import TestCase

from opwen_email_server.utils import path


class GetExtensionTests(TestCase):

    def test_with_simple_extension(self):
        self.assertEqual(path.get_extension('foo.txt'), '.txt')

    def test_without_complex_extension(self):
        self.assertEqual(path.get_extension('foo.txt.gz'), '.txt.gz')

    def test_without_extension(self):
        self.assertEqual(path.get_extension('foo'), '')

    def test_handles_null(self):
        self.assertEqual(path.get_extension(None), '')
        self.assertEqual(path.get_extension(''), '')
