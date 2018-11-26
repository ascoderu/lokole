from unittest import TestCase

from opwen_email_server.services.sendgrid import SendSendgridEmail


class SendgridEmailSenderTests(TestCase):
    recipient1 = 'clemens@lokole.ca'
    recipient2 = 'clemens.wolff@gmail.com'
    sender = 'sendgridtests@lokole.ca'

    def test_sends_email(self):
        send_email = SendSendgridEmail(key='')

        success = send_email({
            'to': [self.recipient1],
            'from': self.sender,
            'subject': self.test_sends_email.__name__,
            'message': 'simple email with <b>formatting</b>'})

        self.assertTrue(success)

    def test_sends_email_with_attachments(self):
        send_email = SendSendgridEmail(key='')

        success = send_email({
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
        send_email = SendSendgridEmail(key='')

        success = send_email({
            'to': [self.recipient1, self.recipient2],
            'from': self.sender,
            'subject': self.test_sends_email_to_multiple_recipients.__name__,
            'message': 'simple email with two recipients'})

        self.assertTrue(success)
