from abc import abstractproperty
from unittest import TestCase

from tests.base import FileWritingTestCaseMixin
from utils.fileformatter import JsonLines


class Base(object):

    class TestFileFormatter(FileWritingTestCaseMixin, TestCase):
        @abstractproperty
        def formatter_class(self):
            raise NotImplementedError

        def test_unable_to_read_from_write_file(self):
            with self.formatter_class(self.new_file(), 'w') as fobj:
                with self.assertRaises(ValueError):
                    list(fobj)

        def test_unable_to_write_to_read_file(self):
            with self.formatter_class(self.new_file(), 'r') as fobj:
                with self.assertRaises(ValueError):
                    fobj.write('foo')

        def test_unable_to_write_to_closed_file(self):
            with self.formatter_class(self.new_file(), 'w') as fobj:
                pass
            with self.assertRaises(ValueError):
                fobj.write('foo')

        def test_unable_to_read_from_closed_file(self):
            with self.formatter_class(self.new_file(), 'r') as fobj:
                pass
            with self.assertRaises(ValueError):
                list(fobj)

        def test_write_read_roundtrip(self):
            filepath = self.new_file()
            expected = [1, {'a': [1, 2]}, 'some string']

            with self.formatter_class(filepath, 'w') as fobj:
                for item in expected:
                    fobj.write(item)
            with self.formatter_class(filepath, 'r') as fobj:
                actual = list(fobj)

            self.assertListEqual(actual, expected)


class TestJsonLines(Base.TestFileFormatter):
    formatter_class = JsonLines
