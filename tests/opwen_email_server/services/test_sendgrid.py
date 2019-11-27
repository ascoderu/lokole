from typing import Optional
from unittest import TestCase
from unittest import skipUnless
from unittest.mock import Mock
from unittest.mock import patch
from urllib.error import URLError

from responses import mock as mock_responses

from opwen_email_server.config import SENDGRID_KEY
from opwen_email_server.services.sendgrid import DeleteSendgridMailbox
from opwen_email_server.services.sendgrid import SendSendgridEmail
from opwen_email_server.services.sendgrid import SetupSendgridMailbox
from tests.opwen_email_server.helpers import MockResponses
from tests.opwen_email_server.helpers import throw


class SendgridEmailSenderTests(TestCase):
    recipient1 = 'clemens@lokole.ca'
    recipient2 = 'clemens.wolff@gmail.com'
    sender = 'sendgridtests@lokole.ca'

    def test_sends_email(self):
        self.assertSendsEmail({
            'to': [self.recipient1], 'from': self.sender, 'subject': self.test_sends_email.__name__, 'body':
            'simple email with <b>formatting</b>'
        })

    def test_sends_email_with_attachments(self):
        self.assertSendsEmail({
            'to': [self.recipient1], 'from':
            self.sender, 'subject':
            self.test_sends_email_with_attachments.__name__, 'body':
            'simple email with attachments', 'attachments':
            [{'filename': 'Some file.txt', 'content': b'first file'},
             {'filename': 'Another file.txt', 'content': b'second file'}]
        })

    def test_sends_email_to_multiple_recipients(self):
        self.assertSendsEmail({
            'to': [self.recipient1, self.recipient2], 'from': self.sender, 'subject':
            self.test_sends_email_to_multiple_recipients.__name__, 'body': 'simple email with two recipients'
        })

    def test_sends_email_to_cc(self):
        self.assertSendsEmail({
            'to': [self.recipient1], 'cc': [self.recipient2], 'from': self.sender, 'subject':
            self.test_sends_email_to_cc.__name__, 'body': 'email with cc'
        })

    def test_sends_email_to_bcc(self):
        self.assertSendsEmail({
            'to': [self.recipient1], 'bcc': [self.recipient2], 'from': self.sender, 'subject':
            self.test_sends_email_to_bcc.__name__, 'body': 'email with bcc'
        })

    def test_client_made_bad_request(self):
        self.assertSendsEmail({'body': self.test_client_made_bad_request.__name__}, success=False, status=400)

    def test_client_had_exception(self):
        self.assertSendsEmail({'body': self.test_client_had_exception.__name__},
                              success=False,
                              exception=URLError('sendgrid error'))

    def test_does_not_send_email_without_key(self):
        action = SendSendgridEmail(key='')

        with patch.object(action, 'log_warning') as mock_log_warning:
            action({'body': 'message'})

        self.assertEqual(mock_log_warning.call_count, 1)

    def assertSendsEmail(self,
                         email: dict,
                         success: bool = True,
                         status: int = 200,
                         exception: Optional[Exception] = None):
        with patch('urllib.request.build_opener') as mock_build_opener:
            self.given_response_status(mock_build_opener, status, exception)

            send_email = SendSendgridEmail(key='fake')

            send_success = send_email(email)

            self.assertTrue(send_success if success else not send_success)

    @classmethod
    def given_response_status(cls, mock_build_opener, status, exception):
        mock_opener = Mock()
        mock_response = Mock()
        mock_build_opener.return_value = mock_opener
        if exception:
            mock_opener.open.side_effect = throw(exception)
        else:
            mock_opener.open.return_value = mock_response
            mock_response.getcode.return_value = status


@skipUnless(SENDGRID_KEY, 'no sendgrid key configured')
class LiveSendgridEmailSenderTests(SendgridEmailSenderTests):
    def assertSendsEmail(self, email: dict, success: bool = True, **kwargs):
        send_email = SendSendgridEmail(key=SENDGRID_KEY, sandbox=True)

        send_success = send_email(email)

        self.assertTrue(send_success if success else not send_success)


class DeleteSendgridMailboxTests(TestCase):
    def test_does_not_make_request_when_key_is_missing(self):
        action = SetupSendgridMailbox(key='', max_retries=1, retry_interval_seconds=1)

        with patch.object(action, 'log_warning') as mock_log_warning:
            action(client_id='', domain='')

        self.assertEqual(mock_log_warning.call_count, 1)

    @mock_responses.activate
    def test_makes_request_when_key_is_set(self):
        mock_responses.add(mock_responses.DELETE, 'https://api.sendgrid.com/v3/user/webhooks/parse/settings/my-domain')

        action = DeleteSendgridMailbox('my-key')

        action('my-client-id', 'my-domain')

        self.assertEqual(len(mock_responses.calls), 1)

    @mock_responses.activate
    def test_handles_missing_mailbox(self):
        mock_responses.add(mock_responses.DELETE,
                           'https://api.sendgrid.com/v3/user/webhooks/parse/settings/my-domain',
                           status=404)

        action = DeleteSendgridMailbox('my-key')

        action('my-client-id', 'my-domain')

        self.assertEqual(len(mock_responses.calls), 1)

    @mock_responses.activate
    def test_throws_on_errors(self):
        mock_responses.add(mock_responses.DELETE,
                           'https://api.sendgrid.com/v3/user/webhooks/parse/settings/my-domain',
                           status=500)

        action = DeleteSendgridMailbox('my-key')

        with self.assertRaises(Exception):
            action('my-client-id', 'my-domain')

        self.assertEqual(len(mock_responses.calls), 1)


class SetupSendgridMailboxTests(TestCase):
    def test_does_not_make_request_when_key_is_missing(self):
        action = SetupSendgridMailbox(key='', max_retries=1, retry_interval_seconds=1)

        with patch.object(action, 'log_warning') as mock_log_warning:
            action(client_id='', domain='')

        self.assertEqual(mock_log_warning.call_count, 1)

    @mock_responses.activate
    def test_makes_request_when_key_is_set(self):
        mock_responses.add(mock_responses.GET,
                           'https://api.sendgrid.com/v3/user/webhooks/parse/settings/my-domain',
                           status=404)
        mock_responses.add(mock_responses.POST, 'https://api.sendgrid.com/v3/user/webhooks/parse/settings', status=200)

        action = SetupSendgridMailbox('my-key', max_retries=1, retry_interval_seconds=1)

        action('my-client-id', 'my-domain')

        self.assertEqual(len(mock_responses.calls), 2)
        self.assertIn(b'"hostname": "my-domain"', mock_responses.calls[1].request.body)

    @mock_responses.activate
    def test_skips_request_when_domain_already_exists(self):
        mock_responses.add(mock_responses.GET,
                           'https://api.sendgrid.com/v3/user/webhooks/parse/settings/my-domain',
                           status=200)

        action = SetupSendgridMailbox('my-key', max_retries=1, retry_interval_seconds=1)

        action('my-client-id', 'my-domain')

        self.assertEqual(len(mock_responses.calls), 1)

    @mock_responses.activate
    def test_retries_request_when_creation_failed(self):
        mock_responses.add(mock_responses.GET,
                           'https://api.sendgrid.com/v3/user/webhooks/parse/settings/my-domain',
                           status=404)
        mock_responses.add_callback(mock_responses.POST,
                                    'https://api.sendgrid.com/v3/user/webhooks/parse/settings',
                                    callback=MockResponses([(500, '', ''), (200, '', '')]))

        action = SetupSendgridMailbox('my-key', max_retries=3, retry_interval_seconds=0.001)

        action('my-client-id', 'my-domain')

        self.assertEqual(len(mock_responses.calls), 4)

    @mock_responses.activate
    def test_fails_request_when_retry_limit_is_exceeded(self):
        mock_responses.add(mock_responses.GET,
                           'https://api.sendgrid.com/v3/user/webhooks/parse/settings/my-domain',
                           status=404)
        mock_responses.add_callback(mock_responses.POST,
                                    'https://api.sendgrid.com/v3/user/webhooks/parse/settings',
                                    callback=MockResponses([(500, '', '') for _ in range(5)]))

        action = SetupSendgridMailbox('my-key', max_retries=3, retry_interval_seconds=0.001)

        with self.assertRaises(Exception):
            action('my-client-id', 'my-domain')
