from os import remove
from os.path import isfile
from tempfile import NamedTemporaryFile
from unittest import TestCase

from opwen_email_server.utils import temporary


class CreateTempFilenameTests(TestCase):
    def test_creates_new_file(self):
        filename = self.when_creating_tempfile()

        self.assertFileExists(filename)

    def test_creates_openable_file(self):
        filename = self.when_creating_tempfile()

        self.assertFileCanBeOpened(filename)

    def test_creates_different_files(self):
        filename1 = self.when_creating_tempfile()
        filename2 = self.when_creating_tempfile()

        self.assertNotEqual(filename1, filename2)

    def setUp(self):
        self._filenames = set()

    def tearDown(self):
        for filename in self._filenames:
            remove(filename)

    def when_creating_tempfile(self):
        filename = temporary.create_tempfilename()
        self._filenames.add(filename)
        return filename

    def assertFileExists(self, filename):
        if not isfile(filename):
            self.fail('file {0} does not exist'.format(filename))

    def assertFileCanBeOpened(self, filename, mode='r'):
        try:
            with open(filename, mode):
                pass
        except EnvironmentError:
            self.fail('unable to open {0}'.format(filename))


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
