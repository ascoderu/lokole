from unittest import TestCase

from opwen_email_client.util.generator import length


class LengthTests(TestCase):
    def test_length(self):
        self.assertEqual(10, length(range(10)))
        self.assertEqual(4, length('abcd'))
