from os import remove
from os.path import isfile
from tempfile import NamedTemporaryFile
from unittest import TestCase

from opwen_email_server.utils import temporary


class CreateTempFilenameTests(TestCase):
    def test_creates_new_file(self):
        filename = temporary.create_tempfilename()

        self.assertFileDoesNotExist(filename)

    def test_creates_different_files(self):
        filename1 = temporary.create_tempfilename()
        filename2 = temporary.create_tempfilename()

        self.assertNotEqual(filename1, filename2)

    def assertFileDoesNotExist(self, filename):
        if isfile(filename):
            self.fail('file {0} exists'.format(filename))


class RemovingTests(TestCase):
    def test_removes_file_when_done(self):
        with NamedTemporaryFile(delete=False) as fobj:
            with temporary.removing(fobj.name) as path:
                pass
            self.assertFileDoesNotExist(path)

    def test_removes_file_only_if_exists(self):
        with NamedTemporaryFile(delete=False) as fobj:
            with temporary.removing(fobj.name) as path:
                remove(path)
            self.assertFileDoesNotExist(path)

    def test_removes_file_on_exception(self):
        with NamedTemporaryFile(delete=False) as fobj:
            with self.assertRaises(ValueError):
                with temporary.removing(fobj.name) as path:
                    raise ValueError
            self.assertFileDoesNotExist(path)

    def assertFileDoesNotExist(self, filename):
        if isfile(filename):
            self.fail('file {0} does exists'.format(filename))
