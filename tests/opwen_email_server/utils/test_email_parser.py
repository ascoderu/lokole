from unittest import TestCase

from os.path import abspath
from os.path import dirname
from os.path import join

from opwen_email_server.utils import email_parser


TEST_DATA_DIRECTORY = abspath(join(
    dirname(__file__), '..', '..',
    'files', 'opwen_email_server', 'utils', 'test_email_parser'))


class ParseMimeEmailTests(TestCase):
    def test_parses_email_metadata(self):
        mime_email = self._given_mime_email('email-html.mime')

        email = email_parser.parse_mime_email(mime_email)

        self.assertEqual(email.get('from'), 'clemens.wolff@gmail.com')
        self.assertEqual(email.get('subject'), 'Two recipients')
        self.assertEqual(email.get('sent_at'), '2017-02-13 06:25')
        self.assertEqual(email.get('to'), ['clemens@victoria.ascoderu.ca',
                                           'laura@victoria.ascoderu.ca'])

    def test_prefers_html_body_over_text(self):
        mime_email = self._given_mime_email('email-html.mime')

        email = email_parser.parse_mime_email(mime_email)

        self.assertEqual(email.get('body'),
                         '<div dir="ltr">Body of the message.</div>\n')

    def test_parses_email_with_cc_and_bcc(self):
        mime_email = self._given_mime_email('email-ccbcc.mime')

        email = email_parser.parse_mime_email(mime_email)

        self.assertEqual(email.get('bcc'), ['laura@ascoderu.ca'])
        self.assertEqual(email.get('cc'), ['nzola@ascoderu.ca',
                                           'clemens@ascoderu.ca'])

    def test_parses_email_with_attachments(self):
        mime_email = self._given_mime_email('email-attachment.mime')

        email = email_parser.parse_mime_email(mime_email)
        attachments = email.get('attachments', [])

        self.assertEqual(len(attachments), 1)
        self.assertStartsWith(attachments[0].get('content'), 'iVBORw0')
        self.assertEqual(attachments[0].get('filename'),
                         'cute-mouse-clipart-mouse4.png')

    @classmethod
    def _given_mime_email(cls, filename, directory=TEST_DATA_DIRECTORY):
        with open(join(directory, filename)) as fobj:
            return fobj.read()

    def assertStartsWith(self, actual, prefix):
        self.assertIsNotNone(actual)
        if not actual.startswith(prefix):
            self.fail('string "{actual}..." does not start with "{prefix}"'
                      .format(actual=actual[:len(prefix)], prefix=prefix))


class GetDomainsTests(TestCase):
    def test_gets_domains(self):
        email = {'to': ['foo@bar.com', 'baz@bar.com', 'foo@com']}

        domains = email_parser.get_domains(email)

        self.assertSetEqual(domains, {'bar.com', 'com'})

    def test_gets_domains_with_cc_and_bcc(self):
        email = {'to': ['foo@bar.com'],
                 'cc': ['baz@bar.com'],
                 'bcc': ['foo@com']}

        domains = email_parser.get_domains(email)

        self.assertSetEqual(domains, {'bar.com', 'com'})


class ConvertImgUrlToBase64(TestCase):
    def test_inlines_image(self):
        input_html = '<img src="https://avatars3.githubusercontent.com/u/16849118?s=400&u=7ddc13a3f746b0fcd633cd0a2367815dc412718a&v=4"/>'
        input_email = {'body': input_html}

        output_email = email_parser.inline_images(input_email)

        self.assertTrue(output_email['body'].startswith('<img src="data:'))
