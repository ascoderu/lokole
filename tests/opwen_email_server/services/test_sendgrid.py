from typing import Optional
from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import patch
from urllib.error import URLError

from responses import mock as mock_responses

from opwen_email_server.services.sendgrid import SendSendgridEmail
from opwen_email_server.services.sendgrid import SetupSendgridMailbox


class SendgridEmailSenderTests(TestCase):
    recipient1 = 'clemens@lokole.ca'
    recipient2 = 'clemens.wolff@gmail.com'
    sender = 'sendgridtests@lokole.ca'

    def test_sends_email(self):
        self.assertSendsEmail({
            'to': [self.recipient1],
            'from': self.sender,
            'subject': self.test_sends_email.__name__,
            'message': 'simple email with <b>formatting</b>'
        })

    def test_sends_email_with_attachments(self):
        self.assertSendsEmail({
            'to': [self.recipient1],
            'from': self.sender,
            'subject': self.test_sends_email_with_attachments.__name__,
            'message': 'simple email with attachments',
            'attachments': [
                {'filename': 'Some file.txt',
                 'content': b'first file'},
                {'filename': 'Another file.txt',
                 'content': b'second file'}]
        })

    def test_sends_email_to_multiple_recipients(self):
        self.assertSendsEmail({
            'to': [self.recipient1, self.recipient2],
            'from': self.sender,
            'subject': self.test_sends_email_to_multiple_recipients.__name__,
            'message': 'simple email with two recipients'
        })

    def test_sends_email_to_cc(self):
        self.assertSendsEmail({
            'to': [self.recipient1],
            'cc': [self.recipient2],
            'from': self.sender,
            'subject': self.test_sends_email_to_cc.__name__,
            'message': 'email with cc'
        })

    def test_sends_email_to_bcc(self):
        self.assertSendsEmail({
            'to': [self.recipient1],
            'bcc': [self.recipient2],
            'from': self.sender,
            'subject': self.test_sends_email_to_bcc.__name__,
            'message': 'email with bcc'
        })

    def test_client_made_bad_request(self):
        self.assertSendsEmail(
            {'message': self.test_client_made_bad_request.__name__},
            success=False,
            status=400)

    def test_client_had_exception(self):
        self.assertSendsEmail(
            {'message': self.test_client_had_exception.__name__},
            success=False,
            exception=URLError('sendgrid error'))

    def test_does_not_send_email_without_key(self):
        action = SendSendgridEmail(key='')

        with patch.object(action, 'log_warning') as mock_log_warning:
            action({'message': 'message'})

        self.assertEqual(mock_log_warning.call_count, 1)

    def assertSendsEmail(self, email: dict, success: bool = True,
                         status: int = 200,
                         exception: Optional[Exception] = None):
        with patch('urllib.request.build_opener') as mock_build_opener:
            self.given_response_status(mock_build_opener, status, exception)

            send_email = SendSendgridEmail(key='fake')

            send_success = send_email(email)

            self.assertTrue(send_success if success else not send_success)

    @classmethod
    def given_response_status(cls, mock_build_opener, status, exception):
        # noinspection PyUnusedLocal
        def raise_exception(*args, **kargs):
            raise exception

        mock_opener = Mock()
        mock_response = Mock()
        mock_build_opener.return_value = mock_opener
        if exception:
            mock_opener.open.side_effect = raise_exception
        else:
            mock_opener.open.return_value = mock_response
            mock_response.getcode.return_value = status


class SetupSendgridMailboxTests(TestCase):
    def test_does_not_make_request_when_key_is_missing(self):
        action = SetupSendgridMailbox(key='')

        with patch.object(action, 'log_warning') as mock_log_warning:
            action(client_id='', domain='')

        self.assertEqual(mock_log_warning.call_count, 1)

    @mock_responses.activate
    def test_makes_request_when_key_is_set(self):
        mock_responses.add(
            mock_responses.POST,
            'https://api.sendgrid.com/v3/user/webhooks/parse/settings')

        action = SetupSendgridMailbox('my-key')

        action('my-client-id', 'my-domain')

        self.assertEqual(len(mock_responses.calls), 1)
        self.assertIn(b'"hostname": "my-domain"',
                      mock_responses.calls[0].request.body)
