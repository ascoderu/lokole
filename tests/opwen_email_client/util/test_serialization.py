from abc import ABCMeta
from abc import abstractmethod
from unittest import TestCase

from opwen_email_client.util.serialization import JsonSerializer


class Base(object):
    class SerializerTests(TestCase, metaclass=ABCMeta):
        @abstractmethod
        def create_serializer(self):
            """
            :rtype: opwen_infrastructure.serialization.Serializer

            """
            raise NotImplementedError

        @property
        def serializable_objects(self):
            """
            :rtype: collections.Iterable

            """
            yield 'some string'
            yield 123.4
            yield [1, "two"]
            yield {'key1': 1, 'key2': ["value2"]}

        def setUp(self):
            self.serializer = self.create_serializer()

        def test_serialization_roundtrip(self):
            for original in self.serializable_objects:
                serialized = self.serializer.serialize(original)
                deserialized = self.serializer.deserialize(serialized)
                self.assertEqual(original, deserialized)


class JsonSerializerTests(Base.SerializerTests):
    def create_serializer(self):
        return JsonSerializer()
