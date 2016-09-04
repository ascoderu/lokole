from unittest import TestCase

from opwen_webapp.helpers.serializers import Serializer
from tests.app_base import AppTestMixin
from tests.base import FileWritingTestCaseMixin
from utils.compressor import ZipCompressor
from utils.fileformatter import JsonLines


class TestRemoteSerializer(FileWritingTestCaseMixin, AppTestMixin, TestCase):
    def setUp(self):
        AppTestMixin.setUp(self)
        FileWritingTestCaseMixin.setUp(self)

    def tearDown(self):
        AppTestMixin.tearDown(self)
        FileWritingTestCaseMixin.tearDown(self)

    def assertAccountsEqual(self, actual, expected):
        """
        :type actual: collections.Iterable[opwen_webapp.models.User]
        :type expected: collections.Iterable[opwen_webapp.models.User]

        """
        for actual, expected in zip(actual, expected):
            self.assertEqual(actual.name, expected.name)
            self.assertEqual(actual.email, expected.email)

    def assertEmailsEqual(self, actual, expected):
        """
        :type actual: collections.Iterable[opwen_webapp.models.Email]
        :type expected: collections.Iterable[opwen_webapp.models.Email]

        """
        for actual, expected in zip(actual, expected):
            self.assertTrue(actual.is_same_as(expected))

    def _new_serializer(self):
        """
        :rtype: Serializer

        """
        app = self.create_app()
        serializer = Serializer(JsonLines, ZipCompressor)
        serializer.init_app(app)
        return serializer

    def test_serialization_deserialization_roundtrip_for_emails(self):
        serializer = self._new_serializer()
        expected_emails = [self.create_complete_email() for _ in range(5)]

        serialized = serializer.serialize(expected_emails)
        actual_emails, actual_accounts = serializer.deserialize(serialized)

        self.paths_created.add(serialized)
        self.assertEqual(actual_accounts, [])
        self.assertEmailsEqual(actual_emails, expected_emails)

    def test_serialization_deserialization_roundtrip_for_accounts(self):
        serializer = self._new_serializer()
        expected_accounts = [self.create_complete_user() for _ in range(5)]

        serialized = serializer.serialize(accounts=expected_accounts)
        actual_emails, actual_accounts = serializer.deserialize(serialized)

        self.paths_created.add(serialized)
        self.assertEqual(actual_emails, [])
        self.assertAccountsEqual(actual_accounts, expected_accounts)

    def test_deserializer_handles_corrupt_archive(self):
        serializer = self._new_serializer()
        serialized = self.new_file(content='not-a-zip-file')

        emails, accounts = serializer.deserialize(serialized)

        self.assertEqual(emails, [])
        self.assertEqual(accounts, [])
