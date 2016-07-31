import os
from tempfile import NamedTemporaryFile
from unittest import TestCase

from utils.checksum import sha256


class TestSha256(TestCase):
    def setUp(self):
        self.files_created = []

    def tearDown(self):
        for filepath in self.files_created:
            os.remove(filepath)

    def _new_file(self, content):
        with NamedTemporaryFile('w', delete=False) as fobj:
            fobj.write(content)
        filepath = fobj.name
        self.files_created.append(filepath)
        return filepath

    def test_same_content_same_hash(self):
        content = 'some content'
        path1 = self._new_file(content)
        path2 = self._new_file(content)

        hash1 = sha256(path1)
        hash2 = sha256(path2)

        self.assertEqual(hash1, hash2)

    def test_different_content_different_hash(self):
        path1 = self._new_file('some content')
        path2 = self._new_file('other content')

        hash1 = sha256(path1)
        hash2 = sha256(path2)

        self.assertNotEqual(hash1, hash2)
