from collections import namedtuple
from unittest import TestCase
from unittest.mock import Mock

from opwen_email_server.services import sendgrid


class SendgridEmailSenderTests(TestCase):
    recipient1 = 'clemens@lokole.ca'
    recipient2 = 'clemens.wolff@gmail.com'
    sender = 'sendgridtests@lokole.ca'

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

    # noinspection PyTypeChecker
    @classmethod
    def _given_client(cls, status_code=202, exception=None):
        mock_client = Mock()

        if exception is None:
            _respond(mock_client.client.mail.send.post, status_code)
        else:
            _raise(mock_client.client.mail.send.post, exception)

        return sendgrid.SendgridEmailSender('fake', mock_client)


def _raise(mock, exception):
    # noinspection PyUnusedLocal
    def raises(*args, **kwargs):
        raise exception
    mock.side_effect = raises


def _respond(mock, status_code, headers=''):
    fakeresponse = namedtuple('Response', 'status_code headers')
    response = fakeresponse(status_code=status_code, headers=headers)
    mock.return_value = response
