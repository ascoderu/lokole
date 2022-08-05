from gzip import GzipFile
from os import remove
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest import TestCase

from opwen_email_client.util.os import backup
from opwen_email_client.util.os import replace_line
from opwen_email_client.util.os import subdirectories


class ReplaceLineTests(TestCase):
    def test_replaces_line(self):
        fobj = NamedTemporaryFile('w+', delete=False)
        try:
            fobj.write('foo\nbar\nbaz')
            fobj.close()

            replace_line(fobj.name, lambda line: line.startswith('ba'), 'changed')

            with open(fobj.name) as changed:
                content = changed.read()
            self.assertEqual(content, 'foo\nchanged\nchanged')
        finally:
            remove(fobj.name)


class SubdirectoriesTests(TestCase):
    def test_handles_missing_directory(self):
        self.assertEqual(len(list(subdirectories('/does-not-exist'))), 0)


class BackupTests(TestCase):
    def test_backup_without_file(self):
        path = '/does/not/exist.txt'
        backup_path = backup(path, suffix='.old')
        self.assertIsNone(backup_path)
        self.assertFalse(Path('{}.old'.format(path)).is_file())

    def test_backup(self):
        fobj = NamedTemporaryFile(delete=False)
        fobj.close()
        path = Path(fobj.name)
        try:
            path.write_bytes(b'foo\n')
            backup(path)

            path.write_bytes(b'bar')
            backup(fobj.name)

            path.write_bytes(b'\nbaz')
            backup_path = backup(fobj.name)

            self.assertIsNotNone(backup_path)
            self.assertTrue(backup_path.is_file())

            with GzipFile(str(backup_path), 'rb') as fobj:
                self.assertEqual(fobj.read(), b'foo\nbar\nbaz')
        finally:
            remove(fobj.name)
