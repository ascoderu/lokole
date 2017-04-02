from urllib.error import URLError

from collections import namedtuple
from unittest import TestCase
from unittest.mock import Mock

from opwen_email_server.services import sendgrid


class SendgridEmailSenderTests(TestCase):
    recipient1 = 'clemens@ascoderu.ca'
    recipient2 = 'clemens.wolff@gmail.com'
    sender = 'sendgridtests@ascoderu.ca'

    def test_sends_email(self):
        sender = self._given_client()

        success = sender.send_email({
            'to': [self.recipient1],
            'from': self.sender,
            'subject': self.test_sends_email.__name__,
            'message': 'simple email with <b>formatting</b>'})

        self.assertTrue(success)

    def test_sends_email_with_attachments(self):
        sender = self._given_client()

        success = sender.send_email({
            'to': [self.recipient1],
            'from': self.sender,
            'subject': self.test_sends_email_with_attachments.__name__,
            'message': 'simple email with attachments',
            'attachments': [
                {'filename': 'Some file.txt',
                 'content': b'first file'},
                {'filename': 'Another file.txt',
                 'content': b'second file'}]})

        self.assertTrue(success)

    def test_sends_email_to_multiple_recipients(self):
        sender = self._given_client()

        success = sender.send_email({
            'to': [self.recipient1, self.recipient2],
            'from': self.sender,
            'subject': self.test_sends_email_to_multiple_recipients.__name__,
            'message': 'simple email with two recipients'})

        self.assertTrue(success)

    def test_calls_error_handler_on_error_response(self):
        on_error_mock = Mock()
        sender = self._given_client(status_code=403, on_error=on_error_mock)

        success = sender.send_email({
            'to': [self.recipient1, self.recipient2],
            'from': self.sender,
            'subject': self.test_calls_error_handler_on_error_response.__name__,
            'message': 'email that gave 403 response'})

        self.assertFalse(success)
        self.assertEqual(on_error_mock.call_count, 1)

    def test_calls_error_handler_on_exception(self):
        on_error_mock = Mock()
        error = URLError('reason')
        sender = self._given_client(exception=error, on_error=on_error_mock)

        success = sender.send_email({
            'to': [self.recipient1, self.recipient2],
            'from': self.sender,
            'subject': self.test_calls_error_handler_on_error_response.__name__,
            'message': 'email that gave 403 response'})

        self.assertFalse(success)
        self.assertEqual(on_error_mock.call_count, 1)

    # noinspection PyTypeChecker
    @classmethod
    def _given_client(cls, status_code=202, on_error=None, exception=None):
        mock_client = Mock()

        if exception is None:
            _respond(mock_client.client.mail.send.post, status_code)
        else:
            _raise(mock_client.client.mail.send.post, exception)

        return sendgrid.SendgridEmailSender('fake', on_error, mock_client)


def _raise(mock, exception):
    # noinspection PyUnusedLocal
    def raises(*args, **kwargs):
        raise exception
    mock.side_effect = raises


def _respond(mock, status_code, headers=''):
    fakeresponse = namedtuple('Response', 'status_code headers')
    response = fakeresponse(status_code=status_code, headers=headers)
    mock.return_value = response
