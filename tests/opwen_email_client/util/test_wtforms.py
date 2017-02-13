from abc import ABCMeta
from abc import abstractmethod
from html import escape
from unittest import TestCase

from wtforms import Form

from opwen_email_client.util.wtforms import HtmlTextAreaField
from opwen_email_client.util.wtforms import SuffixedStringField


class Base(object):
    class FieldTests(TestCase, metaclass=ABCMeta):
        @abstractmethod
        def create_field(self):
            """
            :rtype: wtforms.Field

            """
            raise NotImplementedError

        def verify_field(self, given, expected):
            create_form = make_form(a=self.create_field())

            form = create_form(DummyPostData(a=given))

            self.assertEqual(form['a'].data, expected)
            self.assertEqual(form['a']._value(), expected)


class SuffixedStringFieldTests(Base.FieldTests):
    def create_field(self):
        return SuffixedStringField('bar')

    def test_adds_suffix_when_missing(self):
        self.verify_field('foo', 'foobar')

    def test_does_not_add_suffix_when_existing(self):
        self.verify_field('foobar', 'foobar')


class HtmlTextAreaFieldTests(Base.FieldTests):
    def create_field(self):
        return HtmlTextAreaField()

    @property
    def dangerous_markup(self):
        """
        :rtype: collections.Iterable[(str, str)]

        """
        yield 'foo<script>alert();</script>bar', 'foobar'
        yield 'foo<script type="text/javascript">alert();</script>bar', 'foobar'
        yield 'foo<scr<script>Ha!</script>ipt> alert(document.cookie);</script>bar', 'foobar'

    @property
    def safe_markup(self):
        """
        :rtype: collections.Iterable[(str, str)]

        """
        yield '<h1>Title</h1>', '<h1>Title</h1>'
        yield '<b>bold</b>', '<b>bold</b>'
        yield '<u>underline</u>', '<u>underline</u>'
        yield '<i>italic</i>', '<i>italic</i>'
        yield 'first line<br>second line', 'first line<br>second line'

    def test_is_nullsafe(self):
        self.verify_field('', '')
        self.verify_field(None, '')

    def test_removes_dangerous_markup(self):
        for markup, expected in self.dangerous_markup:
            self.verify_field(markup, expected)

    def test_keeps_safe_markup(self):
        for markup, expected in self.safe_markup:
            self.verify_field(markup, expected)


class EscapedHtmlTextAreaFieldTests(HtmlTextAreaFieldTests):
    @property
    def safe_markup(self):
        for markup, expected in super().safe_markup:
            yield escape(markup), expected

    @property
    def dangerous_markup(self):
        for markup, expected in super().dangerous_markup:
            yield escape(markup), expected


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
