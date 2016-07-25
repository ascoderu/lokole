# -*- coding: utf-8 -*-
from unittest import TestCase

from utils.strings import normalize_caseless


class TestNormalizeCaseless(TestCase):
    def test_same_strings_are_equal(self):
        self.assertNotEqual(normalize_caseless('1'), normalize_caseless('ß'))
        self.assertEqual(normalize_caseless('1'), normalize_caseless('1'))
        self.assertEqual(normalize_caseless('ß'), normalize_caseless('ß'))

    def test_same_strings_are_equal_unicode_normalization(self):
        self.assertNotEqual(normalize_caseless('ê'), normalize_caseless('a'))
        self.assertEqual(normalize_caseless('ê'), normalize_caseless('ê'))
        self.assertEqual(normalize_caseless('Σίσυφος'),
                         normalize_caseless('ΣΊΣΥΦΟΣ'))
