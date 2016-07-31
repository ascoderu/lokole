from os import path
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase

from werkzeug.datastructures import FileStorage

from utils.uploads import UploadNotAllowed
from utils.uploads import Uploads


# noinspection PyMissingConstructor
class TestingFileStorage(FileStorage):
    def __init__(self, filename, content=''):
        """
        :type filename: str
        :type content: str

        """
        self.filename = filename
        self.content = content

    def save(self, dst, **kwargs):
        """
        :type dst: str

        """
        with open(dst, 'w') as f:
            f.write(self.content)


class TestUploads(TestCase):
    def setUp(self):
        self.uploads = Uploads(directory=mkdtemp())

    def tearDown(self):
        rmtree(self.uploads.root_directory)

    def _read(self, filename):
        """
        :type filename: str
        :rtype: str

        """

    def assertDoesUpload(self, file_storage):
        """
        :type file_storage: FileStorage

        """
        uploaded_path = self.uploads.save(file_storage)
        try:
            with open(uploaded_path) as fobj:
                file_content = fobj.read()
        except IOError:
            self.fail('file %s does not exist' % file_storage.filename)

        self.assertEqual(file_content, file_storage.content)

    def assertDidNotUpload(self, file_storage):
        """
        :type file_storage: FileStorage

        """
        bad_path = path.join(self.uploads.root_directory, file_storage.filename)
        self.assertFalse(path.isfile(bad_path))

    def test_save_rejects_disallowed_upload(self):
        disallowed = TestingFileStorage('file.sh')

        with self.assertRaises(UploadNotAllowed):
            self.uploads.save(disallowed)
        self.assertDidNotUpload(disallowed)

    def test_save_stores_upload(self):
        self.assertDoesUpload(TestingFileStorage('file.txt', 'the content'))

    def test_save_does_not_overwrite_upload_with_same_name(self):
        self.assertDoesUpload(TestingFileStorage('file.txt', 'some content'))
        self.assertDoesUpload(TestingFileStorage('file.txt', 'other content'))

    def test_save_is_safe_against_bogus_filenames(self):
        attachment = TestingFileStorage('../file.txt')

        self.uploads.save(attachment)

        self.assertDidNotUpload(attachment)
