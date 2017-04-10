from abc import ABCMeta
from abc import abstractmethod
from json import dumps
from json import loads
from typing import TypeVar

T = TypeVar('T')


class Serializer(metaclass=ABCMeta):
    @abstractmethod
    def serialize(self, obj: T) -> bytes:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def deserialize(self, serialized: bytes) -> T:
        raise NotImplementedError  # pragma: no cover


class JsonSerializer(Serializer):
    _encoding = 'utf-8'
    _separators = (',', ':')

    def serialize(self, obj):
        serialized = dumps(obj, separators=self._separators)
        return serialized.encode(self._encoding)

    def deserialize(self, serialized):
        decoded = serialized.decode(self._encoding)
        return loads(decoded)
