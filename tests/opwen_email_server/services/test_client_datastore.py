from gzip import open as gzip_open
from tempfile import NamedTemporaryFile
from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.services import client_datastore


class UnpackEmailsTests(TestCase):
    @patch.object(client_datastore, 'STORAGE')
    def test_retrieves_compressed_emails(self, storage_mock):
        resource_id = 'c08ddf62-b27c-4de1-ab6f-474d75dc0bfd'
        self.given_gzip_file_with_lines(storage_mock, (
            b'{"to":["foo@test.com"]}',
            b'{"to":["bar@test.com"]}',
        ))

        emails = list(client_datastore.unpack_emails(resource_id))

        self.assertEqual(storage_mock.fetch_file.call_count, 1)
        self.assertListEqual(emails, [{'to': ['foo@test.com']},
                                      {'to': ['bar@test.com']}])

    @classmethod
    def given_gzip_file_with_lines(cls, storage_mock, lines):
        def create_gzip_file(_):
            with NamedTemporaryFile(delete=False) as temp_fobj:
                pass

            with gzip_open(temp_fobj.name, 'wb') as fobj:
                for line in lines:
                    fobj.write(line)
                    fobj.write(b'\n')

            return temp_fobj.name

        storage_mock.fetch_file.side_effect = create_gzip_file
