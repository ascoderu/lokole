from os import remove
from tempfile import NamedTemporaryFile
from unittest import TestCase

from opwen_email_client.util.os import replace_line
from opwen_email_client.util.os import subdirectories


class ReplaceLinetests(TestCase):
    def test_replaces_line(self):
        fobj = NamedTemporaryFile('w+', delete=False)
        try:
            fobj.write('foo\nbar\nbaz')
            fobj.close()

            replace_line(
                fobj.name,
                lambda line: line.startswith('ba'),
                'changed')

            with open(fobj.name) as changed:
                content = changed.read()
            self.assertEqual(content, 'foo\nchanged\nchanged')
        finally:
            remove(fobj.name)


class SubdirectoriesTests(TestCase):
    def test_handles_missing_directory(self):
        self.assertEqual(len(list(subdirectories('/does-not-exist'))), 0)
