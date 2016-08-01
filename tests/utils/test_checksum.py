from unittest import TestCase

from tests.base import FileWritingTestCaseMixin
from utils.checksum import sha256


class TestSha256(FileWritingTestCaseMixin, TestCase):
    def test_same_content_same_hash(self):
        content = 'some content'
        path1 = self.new_file(content=content)
        path2 = self.new_file(content=content)

        hash1 = sha256(path1)
        hash2 = sha256(path2)

        self.assertEqual(hash1, hash2)

    def test_different_content_different_hash(self):
        path1 = self.new_file(content='some content')
        path2 = self.new_file(content='other content')

        hash1 = sha256(path1)
        hash2 = sha256(path2)

        self.assertNotEqual(hash1, hash2)
