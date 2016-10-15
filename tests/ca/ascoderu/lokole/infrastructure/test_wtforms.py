from unittest import TestCase

from wtforms import Form

from ca.ascoderu.lokole.infrastructure.wtforms import SuffixedStringField


class SuffixedStringFieldTests(TestCase):
    def test_adds_suffix_when_missing(self):
        create_form = make_form(a=SuffixedStringField('bar'))

        form = create_form(DummyPostData(a='foo'))

        self.assertEqual(form['a'].data, 'foobar')
        self.assertEqual(form['a']._value(), 'foobar')

    def test_does_not_add_suffix_when_existing(self):
        create_form = make_form(a=SuffixedStringField('bar'))

        form = create_form(DummyPostData(a='foobar'))

        self.assertEqual(form['a'].data, 'foobar')
        self.assertEqual(form['a']._value(), 'foobar')


class DummyPostData(dict):
    """
    Taken from https://github.com/wtforms/wtforms/blob/f5ef784caf/tests/common.py

    """
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


def make_form(_name='F', **fields):
    """
    Taken from https://github.com/wtforms/wtforms/blob/f5ef784caf/tests/fields.py

    """
    return type(str(_name), (Form, ), fields)
