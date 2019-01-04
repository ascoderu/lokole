from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import patch

from opwen_email_server.services.sendgrid import SendSendgridEmail


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

    def test_client_made_bad_request(self):
        self.assertSendsEmail(
            {'message': self.test_client_made_bad_request.__name__},
            success=False,
            status=400)

    def assertSendsEmail(self, email: dict, success: bool = True, status: int = 200):
        with patch('urllib.request.build_opener') as mock_build_opener:
            self.given_response_status(mock_build_opener, status)

            send_email = SendSendgridEmail(key='fake')

            send_success = send_email(email)

            self.assertTrue(send_success if success else not send_success)

    @classmethod
    def given_response_status(cls, mock_build_opener, status):
        mock_opener = Mock()
        mock_response = Mock()
        mock_build_opener.return_value = mock_opener
        mock_opener.open.return_value = mock_response
        mock_response.getcode.return_value = status
