from unittest import TestCase

from opwen_email_server.utils.env import Env


class EnvTests(TestCase):
    def test_get_string(self):
        env = Env({'foo': 'bar'})
        self.assertEqual(env('foo'), 'bar')
        self.assertEqual(env('missing'), '')

    def test_get_integer(self):
        env = Env({'foo': '123'})
        self.assertEqual(env.integer('foo'), 123)
        self.assertEqual(env.integer('missing'), 0)

    def test_get_boolean(self):
        env = Env({'foo': 'True'})
        self.assertEqual(env.boolean('foo'), True)
        self.assertEqual(env.boolean('missing'), False)

    def test_get_urlpart(self):
        env = Env({'foo': 'ba/r'})
        self.assertEqual(env.urlpart('foo'), 'ba%2Fr')
        self.assertEqual(env.urlpart('missing'), '')
