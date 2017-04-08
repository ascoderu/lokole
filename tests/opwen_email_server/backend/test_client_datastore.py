from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.backend import client_datastore


class UnpackEmailsTests(TestCase):
    @patch.object(client_datastore, 'STORAGE')
    def test_retrieves_compressed_emails(self, storage_mock):
        resource_id = 'c08ddf62-b27c-4de1-ab6f-474d75dc0bfd'
        self.given_objects(storage_mock, (
            {'to': ['foo@test.com']},
            {'to': ['bar@test.com']},
        ))

        emails = list(client_datastore.unpack_emails(resource_id))

        self.assertEqual(storage_mock.fetch_objects.call_count, 1)
        self.assertListEqual(emails, [{'to': ['foo@test.com']},
                                      {'to': ['bar@test.com']}])

    @classmethod
    def given_objects(cls, storage_mock, objs):
        storage_mock.fetch_objects.return_value = objs
