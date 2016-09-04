from collections import namedtuple
from datetime import datetime
from unittest import TestCase

from opwen_webapp.helpers.filters import render_date
from opwen_webapp.helpers.filters import safe_multiline
from opwen_webapp.helpers.filters import sort_by_date


class TestRenderDate(TestCase):
    # noinspection PyTypeChecker
    def test_handles_none_date(self):
        self.assertEqual(render_date(None), '')

    def test_renders_date(self):
        self.assertTrue(render_date(datetime.now()))


# noinspection PyPep8Naming
class TestSafeMultiline(TestCase):
    @property
    def _contexts(self):
        context = namedtuple('Context', 'autoescape')
        yield context(autoescape=True)
        yield context(autoescape=False)

    def assertHasParagraphs(self, text, num_paragraphs):
        paragraph_starts = text.count('<p>')
        paragraph_ends = text.count('</p>')
        self.assertEqual(paragraph_starts, paragraph_ends)
        self.assertEqual(num_paragraphs, paragraph_starts)

    def assertHasExtraLines(self, text, num_lines):
        self.assertEqual(text.count('<br>'), num_lines)

    def test_renders_newlines(self):
        for context in self._contexts:
            text = safe_multiline(context, 'one\ntwo\nthree')

            self.assertHasParagraphs(text, 1)
            self.assertHasExtraLines(text, 2)

    def test_renders_paragraphs(self):
        for context in self._contexts:
            text = safe_multiline(context, 'para\n\ngraph')

            self.assertHasParagraphs(text, 2)
            self.assertHasExtraLines(text, 0)


class TestSortByDate(TestCase):
    _new_has_date = namedtuple('HasDate', 'date')
    _new_has_no_date = namedtuple('HasNoDate', 'some_attribute')

    def test_no_date_object_gets_sorted_first(self):
        date1 = self._new_has_date(datetime(2000, 1, 1))
        date2 = self._new_has_date(datetime(2000, 2, 2))
        nodate1 = None
        nodate2 = self._new_has_no_date('no-date')
        given = [date1, nodate1, date2, nodate2]

        actual1 = sort_by_date(given, reverse=True)
        self.assertSequenceEqual(actual1, [nodate1, nodate2, date2, date1])

        actual2 = sort_by_date(given, reverse=False)
        self.assertSequenceEqual(actual2, [date1, date2, nodate1, nodate2])
