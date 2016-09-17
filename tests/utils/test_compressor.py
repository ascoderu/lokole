from abc import abstractproperty
from os import path
from unittest import TestCase

from tests.base import FileWritingTestCaseMixin
from utils.compressor import ZipCompressor


class Base(object):

    class TestDirectoryCompressor(FileWritingTestCaseMixin, TestCase):
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

        def test_raises_valueerror_on_bad_archive(self):
            archive = self.new_file(content='not-an-archive')
            directory = self.new_directory()

            with self.assertRaises(ValueError):
                self.compressor.decompress(archive, 'file', directory)

        def test_raises_keyerror_on_unknown_file(self):
            filepath = self.new_file(content='some content')
            archive = self.compressor.compress(path.dirname(filepath))
            directory = self.new_directory()
            self.paths_created.add(archive)

            with self.assertRaises(ValueError):
                self.compressor.decompress(archive, 'file', directory)


class TestZipCompressor(Base.TestDirectoryCompressor):
    compressor = ZipCompressor()
