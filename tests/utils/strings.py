# -*- coding: utf-8 -*-
from unittest import TestCase

from utils import strings


class TestIstreq(TestCase):
    def test_none_not_equal(self):
        self.assertFalse(strings.istreq('1', None))
        self.assertFalse(strings.istreq(None, '1'))
        self.assertTrue(strings.istreq(None, None))

    def test_non_string_types_not_equal(self):
        self.assertFalse(strings.istreq(1, 1))
        self.assertFalse(strings.istreq(1, '1'))
        self.assertFalse(strings.istreq('1', 1))

    def test_same_strings_are_equal(self):
        self.assertFalse(strings.istreq('1', 'ß'))
        self.assertTrue(strings.istreq('1', '1'))
        self.assertTrue(strings.istreq('ß', 'ß'))

    def test_same_strings_are_equal_unicode_normalization(self):
        self.assertFalse(strings.istreq('ê', 'a'))
        self.assertTrue(strings.istreq('ê', 'ê'))
        self.assertTrue(strings.istreq('Σίσυφος', 'ΣΊΣΥΦΟΣ'))
