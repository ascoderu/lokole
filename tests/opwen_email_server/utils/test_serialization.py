from unittest import TestCase

from opwen_email_server.utils import serialization


class ToJsonTests(TestCase):
    def test_creates_slim_json(self):
        serialized = serialization.to_json({'a': 1, 'b': 2})

        self.assertNotIn('\n', serialized)
        self.assertNotIn(' ', serialized)
