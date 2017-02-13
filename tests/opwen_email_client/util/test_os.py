from unittest import TestCase

from opwen_email_client.util.os import subdirectories


class SubdirectoriesTests(TestCase):
    def test_handles_missing_directory(self):
        self.assertEqual(len(list(subdirectories('/does-not-exist'))), 0)
