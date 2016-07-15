# -*- coding: utf-8 -*-
from unittest import TestCase

from utils.strings import istreq


class TestIstreq(TestCase):
    def test_none_not_equal(self):
        self.assertFalse(istreq('1', None))
        self.assertFalse(istreq(None, '1'))
        self.assertTrue(istreq(None, None))

    def test_non_string_types_not_equal(self):
        self.assertFalse(istreq(1, 1))
        self.assertFalse(istreq(1, '1'))
        self.assertFalse(istreq('1', 1))

    def test_same_strings_are_equal(self):
        self.assertFalse(istreq('1', 'ß'))
        self.assertTrue(istreq('1', '1'))
        self.assertTrue(istreq('ß', 'ß'))

    def test_same_strings_are_equal_unicode_normalization(self):
        self.assertFalse(istreq('ê', 'a'))
        self.assertTrue(istreq('ê', 'ê'))
        self.assertTrue(istreq('Σίσυφος', 'ΣΊΣΥΦΟΣ'))
