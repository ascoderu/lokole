from os import remove
from os.path import isfile
from tempfile import NamedTemporaryFile
from unittest import TestCase

from opwen_email_server.utils import temporary


class CreateTempFilenameTests(TestCase):
    def test_creates_new_file(self):
        filename = temporary.create_tempfilename()

        self.assertFileDoesNotExist(filename)

    def test_creates_new_file_preserving_extension(self):
        filename = temporary.create_tempfilename('foo.txt')

        self.assertHasExtension(filename, '.txt')

    def test_creates_new_file_preserving_multi_extension(self):
        filename = temporary.create_tempfilename('foo.tar.gz')

        self.assertHasExtension(filename, '.tar.gz')

    def test_creates_new_file_handling_bad_extension(self):
        filename = temporary.create_tempfilename('/foo/bar.gz')

        self.assertHasExtension(filename, '.gz')
        self.assertPathDoesNotContain(filename, '/foo/')

    def test_creates_different_files(self):
        filename1 = temporary.create_tempfilename()
        filename2 = temporary.create_tempfilename()

        self.assertNotEqual(filename1, filename2)

    def assertFileDoesNotExist(self, filename):
        if isfile(filename):
            self.fail(f'file {filename} exists')

    def assertPathDoesNotContain(self, filename, part):
        self.assertTrue(part not in filename, f'{filename} has path part {part}')

    def assertHasExtension(self, filename, extension):
        self.assertTrue(filename.endswith(extension), f'{filename} does not have extension {extension}')


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
            self.fail(f'file {filename} does exists')
