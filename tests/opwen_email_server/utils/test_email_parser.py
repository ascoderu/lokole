from enum import Enum
from enum import unique
from os.path import abspath
from os.path import dirname
from os.path import join
from unittest import TestCase
from unittest.mock import patch

from responses import mock as mock_responses

from opwen_email_server.utils import email_parser
from tests.opwen_email_server.helpers import throw

TEST_DATA_DIRECTORY = abspath(
    join(dirname(__file__), '..', '..', 'files', 'opwen_email_server', 'utils', 'test_email_parser'))


@unique
class ImageSize(Enum):
    large = 1
    small = 2


def _given_test_image(size: ImageSize) -> bytes:
    image_path = join(TEST_DATA_DIRECTORY, f'{size.name}.png')
    with open(image_path, 'rb') as fobj:
        return fobj.read()


class ParseMimeEmailTests(TestCase):
    def test_parses_email_metadata(self):
        mime_email = self._given_mime_email('email-html.mime')

        email = self._parse(mime_email)

        self.assertEqual(email.get('from'), 'clemens.wolff@gmail.com')
        self.assertEqual(email.get('subject'), 'Two recipients')
        self.assertEqual(email.get('sent_at'), '2017-02-13 06:25')
        self.assertEqual(email.get('to'), ['clemens@victoria.lokole.ca', 'laura@victoria.lokole.ca'])

    def test_prefers_html_body_over_text(self):
        mime_email = self._given_mime_email('email-html.mime')

        email = self._parse(mime_email)

        self.assertEqual(email.get('body'), '<div dir="ltr">Body of the message.</div>\n')

    def test_parses_email_with_cc_and_bcc(self):
        mime_email = self._given_mime_email('email-ccbcc.mime')

        email = self._parse(mime_email)

        self.assertEqual(email.get('bcc'), ['laura@lokole.ca'])
        self.assertEqual(email.get('cc'), ['clemens@lokole.ca', 'nzola@lokole.ca'])

    def test_parses_email_with_attachments(self):
        mime_email = self._given_mime_email('email-attachment.mime')

        email = self._parse(mime_email)
        attachments = email.get('attachments', [])

        self.assertEqual(len(attachments), 1)
        self.assertGreater(len(attachments[0].get('content')), 0)
        self.assertEqual(attachments[0].get('filename'), 'cute-mouse-clipart-mouse4.png')
        self.assertNotIn('id', attachments[0])

    def test_cid(self):
        mime_email = self._given_mime_email('email-cid.mime')

        email = self._parse(mime_email)
        attachments = email.get('attachments', [])

        self.assertEqual(len(attachments), 2)
        self.assertIsNotNone(attachments[0].get('cid'))
        self.assertIsNotNone(attachments[1].get('cid'))
        self.assertNotEqual(attachments[0]['cid'], attachments[1]['cid'])

    @classmethod
    def _parse(cls, mime_email):
        return email_parser.parse_mime_email(mime_email)

    @classmethod
    def _given_mime_email(cls, filename, directory=TEST_DATA_DIRECTORY):
        with open(join(directory, filename)) as fobj:
            return fobj.read()


class MimeEmailParserTests(ParseMimeEmailTests):
    _parse = email_parser.MimeEmailParser()


class GetDomainsTests(TestCase):
    def test_gets_domains(self):
        email = {'to': ['foo@bar.com', 'baz@bar.com', 'foo@com']}

        domains = email_parser.get_domains(email)

        self.assertSetEqual(set(domains), {'bar.com', 'com'})

    def test_gets_domains_with_cc_and_bcc(self):
        email = {'to': ['foo@bar.com'], 'cc': ['baz@bar.com'], 'bcc': ['foo@com']}

        domains = email_parser.get_domains(email)

        self.assertSetEqual(set(domains), {'bar.com', 'com'})


class GetReceipientsTests(TestCase):
    def test_get_recipients(self):
        email = {'to': ['foo@bar.com'], 'cc': ['baz@bar.com', 'foo@com']}

        recipients = email_parser.get_recipients(email)

        self.assertSetEqual(set(recipients), {'foo@bar.com', 'baz@bar.com', 'foo@com'})


class ResizeImageTests(TestCase):
    error_message = 'If default MAX_WIDTH_IMAGES and/or MAX_HEIGHT_IMAGES were changed ' \
                    'you may need to change the test base64 in "images_base64.json".'

    def test_change_image_size(self):
        input_bytes = _given_test_image(size=ImageSize.large)
        output_bytes = email_parser._change_image_size(input_bytes)
        self.assertNotEqual(input_bytes, output_bytes, self.error_message)

    def test_change_image_size_when_already_small(self):
        input_bytes = _given_test_image(size=ImageSize.small)
        output_bytes = email_parser._change_image_size(input_bytes)
        self.assertEqual(input_bytes, output_bytes, self.error_message)


class ConvertImgUrlToBase64Tests(TestCase):
    @mock_responses.activate
    def test_format_inline_images_with_img_tag(self):
        self.givenTestImage()
        input_email = {'body': '<div><h3>test image</h3><img src="http://test-url.png"/></div>'}

        output_email = email_parser.format_inline_images(input_email, self.fail_if_called)

        self.assertStartsWith(output_email['body'], '<div><h3>test image</h3><img src="data:image/png;')

    @mock_responses.activate
    def test_format_inline_images_with_query_string(self):
        url = 'http://test-url.png?foo=bar&baz=qux'
        self.givenTestImage(url=url, content_type='')
        input_email = {'body': f'<div><h3>test image</h3><img src="{url}"/></div>'}

        output_email = email_parser.format_inline_images(input_email, self.fail_if_called)

        self.assertStartsWith(output_email['body'], '<div><h3>test image</h3><img src="data:image/png;')

    @mock_responses.activate
    @patch.object(email_parser, 'Image')
    def test_handles_exceptions_when_processing_image(self, mock_pil):
        mock_pil.open.side_effect = throw(IOError())
        handled_errors = []

        def on_error(*args):
            handled_errors.append(args)

        self.givenTestImage()
        input_email = {'body': '<div><h3>test image</h3><img src="http://test-url.png"/></div>'}

        output_email = email_parser.format_inline_images(input_email, on_error)

        self.assertEqual(len(handled_errors), 1)
        self.assertEqual(output_email, input_email)

    def test_format_inline_images_with_img_tag_without_src_attribute(self):
        input_email = {'body': '<div><img/></div>'}

        output_email = email_parser.format_inline_images(input_email, self.fail_if_called)

        self.assertEqual(output_email, input_email)

    def test_format_inline_images_with_img_tag_and_invalid_src_attribute(self):
        input_email = {'body': '<div><img src="foo:invalid"/></div>'}

        output_email = email_parser.format_inline_images(input_email, self.fail_if_called)

        self.assertEqual(output_email, input_email)

    @mock_responses.activate
    def test_format_inline_images_with_bad_request(self):
        self.givenTestImage(status=404)
        input_email = {'body': '<div><img src="http://test-url.png"/></div>'}

        output_email = email_parser.format_inline_images(input_email, self.fail_if_called)

        self.assertEqual(output_email, input_email)

    @mock_responses.activate
    def test_format_inline_images_with_many_img_tags(self):
        self.givenTestImage()
        input_email = {'body': '<div><img src="http://test-url.png"/><img src="http://test-url.png"/></div>'}

        output_email = email_parser.format_inline_images(input_email, self.fail_if_called)

        self.assertHasCount(output_email['body'], 'src="data:', 2)

    def test_format_inline_images_without_img_tags(self):
        input_email = {'body': '<div></div>'}

        output_email = email_parser.format_inline_images(input_email, self.fail_if_called)

        self.assertEqual(output_email, input_email)

    @mock_responses.activate
    def test_format_inline_images_without_content_type(self):
        self.givenTestImage(content_type='')
        input_email = {'body': '<div><img src="http://test-url.png"/></div>'}

        output_email = email_parser.format_inline_images(input_email, self.fail_if_called)

        self.assertStartsWith(output_email['body'], '<div><img src="data:image/png;')

    def assertStartsWith(self, data, prefix):
        self.assertEqual(data[:len(prefix)], prefix)

    def assertHasCount(self, data, snippet, expected_count):
        actual_count = data.count(snippet)
        self.assertEqual(actual_count, expected_count, f'Expected {snippet} to occur {expected_count} '
                         f'times but got {actual_count}')

    @classmethod
    def givenTestImage(cls, content_type='image/png', status=200, url='http://test-url.png'):
        with open(join(TEST_DATA_DIRECTORY, 'test_image.png'), 'rb') as image:
            image_bytes = image.read()

        mock_responses.add(
            mock_responses.GET,
            url,
            content_type=content_type,
            body=image_bytes,
            status=status,
        )

    def fail_if_called(self, message, *args):
        self.fail(message % args)


class EnsureHasSentAtTests(TestCase):
    def test_sets_sent_at_if_missing(self):
        input_email = {}

        email_parser.ensure_has_sent_at(input_email)

        self.assertIn('sent_at', input_email)
        self.assertEqual(len(input_email['sent_at']), 16)

    def test_sets_sent_at_if_empty(self):
        input_email = {'sent_at': ''}

        email_parser.ensure_has_sent_at(input_email)

        self.assertIn('sent_at', input_email)
        self.assertEqual(len(input_email['sent_at']), 16)

    def test_respects_sent_at_if_existing(self):
        sent_at = '2020-02-01 21:09'
        input_email = {'sent_at': sent_at}

        email_parser.ensure_has_sent_at(input_email)

        self.assertEqual(input_email['sent_at'], sent_at)


class FormatAttachedFilesTests(TestCase):
    def test_format_attachments_without_attachment(self):
        input_email = {'attachments': []}

        output_email = email_parser.format_attachments(input_email)

        self.assertEqual(input_email, output_email)

    def test_format_attachments_with_image(self):
        input_filename = 'test_image.png'
        input_content = _given_test_image(size=ImageSize.large)
        attachment = {'filename': input_filename, 'content': input_content}
        input_email = {'attachments': [attachment]}

        output_email = email_parser.format_attachments(input_email)
        output_attachments = output_email.get('attachments', '')

        self.assertEqual(len(output_attachments), 1)

        output_filename = output_attachments[0].get('filename', '')
        output_content = output_attachments[0].get('content', '')

        self.assertNotEqual(input_content, output_content)
        self.assertEqual(input_filename, output_filename)


class DescendingTimestampTests(TestCase):
    def test_descending_timestamp_correct(self):
        sent_at = '2020-02-01 21:09'

        sent_at_timestamp = email_parser.descending_timestamp(sent_at)

        self.assertEqual(sent_at_timestamp, '519408660')

    def test_descending_timestamp_order_by_year(self):
        january_2020 = '2020-01-01 22:09'
        january_2021 = '2021-01-01 22:09'

        january_2020_timestamp = email_parser.descending_timestamp(january_2020)
        january_2021_timestamp = email_parser.descending_timestamp(january_2021)

        timestamp_ordering = sorted([january_2020_timestamp, january_2021_timestamp])
        self.assertEqual(timestamp_ordering, [january_2021_timestamp, january_2020_timestamp])

    def test_descending_timestamp_order_by_month(self):
        january = '2020-01-01 22:09'
        february = '2020-02-02 22:09'

        january_timestamp = email_parser.descending_timestamp(january)
        february_timestamp = email_parser.descending_timestamp(february)

        timestamp_ordering = sorted([january_timestamp, february_timestamp])
        self.assertEqual(timestamp_ordering, [february_timestamp, january_timestamp])

    def test_descending_timestamp_order_by_day(self):
        january_1st = '2020-01-01 22:09'
        january_2nd = '2020-01-02 22:09'

        january_1_timestamp = email_parser.descending_timestamp(january_1st)
        january_2_timestamp = email_parser.descending_timestamp(january_2nd)

        timestamp_ordering = sorted([january_1_timestamp, january_2_timestamp])
        self.assertEqual(timestamp_ordering, [january_2_timestamp, january_1_timestamp])

    def test_descending_timestamp_order_by_hour(self):
        january_1st_22h09m = '2020-01-01 22:09'
        january_1st_23h09m = '2020-01-01 23:09'

        january_22h09m_timestamp = email_parser.descending_timestamp(january_1st_22h09m)
        january_23h09m_timestamp = email_parser.descending_timestamp(january_1st_23h09m)

        timestamp_ordering = sorted([january_22h09m_timestamp, january_23h09m_timestamp])
        self.assertEqual(timestamp_ordering, [january_23h09m_timestamp, january_22h09m_timestamp])

    def test_descending_timestamp_order_by_minute(self):
        january_1st_22h09m = '2020-01-01 22:09'
        january_1st_22h11m = '2020-01-01 22:11'

        january_22h09m_timestamp = email_parser.descending_timestamp(january_1st_22h09m)
        january_22h11m_timestamp = email_parser.descending_timestamp(january_1st_22h11m)

        timestamp_ordering = sorted([january_22h09m_timestamp, january_22h11m_timestamp])
        self.assertEqual(timestamp_ordering, [january_22h11m_timestamp, january_22h09m_timestamp])
