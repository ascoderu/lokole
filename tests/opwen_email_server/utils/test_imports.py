from unittest import TestCase

from opwen_email_server.utils.imports import can_import


class CanImportTests(TestCase):
    def test_true_for_existing_module(self):
        self.assertTrue(can_import('collections'))

    def test_false_for_missing_module(self):
        self.assertFalse(can_import('really_not_a_module'))
