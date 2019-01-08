from os import environ, remove
from tempfile import NamedTemporaryFile
from typing import Iterable
from unittest import TestCase

from opwen_email_client.util.os import getenv
from opwen_email_client.util.os import subdirectories
from opwen_email_client.util.os import replace_line


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


class GetenvTests(TestCase):
    def setUp(self):
        self.envs = set()

    def tearDown(self):
        for env in self.envs:
            del environ[env]

    @classmethod
    def unknown_types(cls) -> Iterable[object]:
        yield "foo"
        yield "[1,"

    @classmethod
    def known_types(cls) -> Iterable[object]:
        yield True
        yield [1, 2]
        yield {'a': 'b'}

    def given_env(self, key: str, value: object):
        environ[key] = str(value)
        self.envs.add(key)

    def test_parses_known_types(self):
        for i, expected in enumerate(self.known_types()):
            env_key = 'known_type_{}'.format(i)

            self.given_env(env_key, expected)

            actual = getenv(env_key)

            self.assertEqual(actual, expected)

    def test_passes_through_unknown_types(self):
        for i, expected in enumerate(self.unknown_types()):
            env_key = 'unknown_type_{}'.format(i)

            self.given_env(env_key, expected)

            actual = getenv(env_key)

            self.assertEqual(actual, expected)

    def test_returns_default_when_key_is_missing(self):
        default = 123

        actual = getenv('missing_key', default)

        self.assertEqual(actual, default)
