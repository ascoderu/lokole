from abc import ABCMeta
from abc import abstractmethod
from copy import deepcopy
from unittest import TestCase

from typing import Iterable

from opwen_email_client.util.serialization import JsonSerializer
from opwen_email_client.util.serialization import Serializer


class Base(object):
    class SerializerTests(TestCase, metaclass=ABCMeta):
        @abstractmethod
        def create_serializer(self) -> Serializer:
            raise NotImplementedError

        @property
        def serializable_objects(self) -> Iterable:
            yield {'key1': 1, 'key2': ["value2"]}, ''
            yield {'attachments': [{'content': b'content'}]}, 'email'
            yield {'content': b'content'}, 'attachment'

        def setUp(self):
            self.serializer = self.create_serializer()

        def test_serialization_roundtrip(self):
            for original, type_ in self.serializable_objects:
                serialized = self.serializer.serialize(deepcopy(original), type_)
                deserialized = self.serializer.deserialize(serialized, type_)
                self.assertEqual(original, deserialized)


class JsonSerializerTests(Base.SerializerTests):
    def create_serializer(self):
        return JsonSerializer()
