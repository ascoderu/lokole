from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.api import email_sender


class SendTests(TestCase):
    @patch.object(email_sender, 'EMAIL')
    def test_success(self, sender_mock):
        sender_mock.send_email.return_value = True
        email = {'to': ['foo@test.com']}

        message, code = email_sender.send(email)

        self.assertEqual(code, 200)

    @patch.object(email_sender, 'EMAIL')
    def test_failure(self, sender_mock):
        sender_mock.send_email.return_value = False
        email = {'to': ['foo@test.com']}

        message, code = email_sender.send(email)

        self.assertNotEqual(code, 200)
