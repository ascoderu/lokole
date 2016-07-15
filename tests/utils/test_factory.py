from unittest import TestCase

from utils.factory import DynamicFactory


class SomeObject(object):
    pass


class TestDynamicFactory(TestCase):
    def test_passes_through_constructor(self):
        clazz = SomeObject
        self.assertIsInstance(DynamicFactory(clazz)(), SomeObject)

    def test_locates_module(self):
        module = '%s.%s' % (SomeObject.__module__, SomeObject.__name__)
        self.assertIsInstance(DynamicFactory(module)(), SomeObject)
