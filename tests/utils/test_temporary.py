from unittest import TestCase

from tests.base import FileWritingTestCaseMixin
from utils.temporary import SafeNamedTemporaryFile
from utils.temporary import create_temporary_directory
from utils.temporary import removing


class TestCreateTemporaryDirectory(FileWritingTestCaseMixin, TestCase):
    def test_creates_new_directory_and_cleans_up_on_exit(self):
        with create_temporary_directory() as directory:
            self.assertDirectoryExists(directory)
        self.assertDirectoryDoesNotExist(directory)

    def test_creates_new_directory_and_does_not_clean_up_if_instructed(self):
        with create_temporary_directory(delete=False) as directory:
            self.assertDirectoryExists(directory)
        self.assertDirectoryExists(directory)


class TestRemoving(FileWritingTestCaseMixin, TestCase):
    def test_removing_removes_file(self):
        with removing(self.new_file()) as filepath:
            self.assertFileExists(filepath)
        self.assertFileDoesNotExist(filepath)

    def test_removing_removes_directory(self):
        with removing(self.new_directory()) as filepath:
            self.assertDirectoryExists(filepath)
        self.assertDirectoryDoesNotExist(filepath)


class TestSafeNamedTemporaryFile(FileWritingTestCaseMixin, TestCase):
    def test_does_not_create_file_on_exception(self):
        with self.assertRaises(Exception):
            with SafeNamedTemporaryFile('w', delete=False) as fobj:
                self.assertFileExists(fobj.name)
                raise ValueError
        self.assertFileDoesNotExist(fobj.name)
