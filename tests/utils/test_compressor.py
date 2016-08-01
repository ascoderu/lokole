from abc import abstractproperty
from os import path
from unittest import TestCase

from tests.base import FileWritingTestCaseMixin
from utils.compressor import ZipCompressor


class TestDirectoryCompressor(FileWritingTestCaseMixin, TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = None
        if self.__class__ != TestDirectoryCompressor:
            # noinspection PyUnresolvedReferences
            self.run = TestCase.run.__get__(self, self.__class__)
        else:
            self.run = lambda this, *ar, **kw: None

    @abstractproperty
    def compressor(self):
        """
        :rtype: utils.compressor.DirectoryCompressor

        """
        raise NotImplementedError

    def test_create_archive(self):
        directory = self.new_directory()
        self.new_file(directory)
        self.new_file(directory)

        archive = self.compressor.compress(directory)

        self.assertFileExists(archive)

    def test_extract_from_archive(self):
        content = 'some content'
        filepath = self.new_file(content=content)

        archive = self.compressor.compress(path.dirname(filepath))
        self.assertFileExists(archive)

        extracted = self.compressor.decompress(
            archive_path=archive,
            filename=path.basename(filepath),
            to_directory=self.new_directory())
        self.assertFileExists(extracted)
        self.assertFileContentEqual(extracted, content)


class TestZipCompressor(TestDirectoryCompressor):
    compressor = ZipCompressor()
