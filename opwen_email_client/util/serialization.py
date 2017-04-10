from abc import ABCMeta
from abc import abstractmethod
import json


class Serializer(metaclass=ABCMeta):
    @abstractmethod
    def serialize(self, obj):
        """
        :type obj: T
        :rtype: bytes

        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def deserialize(self, serialized):
        """
        :type serialized: bytes
        :rtype: T

        """
        raise NotImplementedError  # pragma: no cover


class JsonSerializer(Serializer):
    _encoding = 'utf-8'
    _separators = (',', ':')

    def serialize(self, obj):
        serialized = json.dumps(obj, separators=self._separators)
        return serialized.encode(self._encoding)

    def deserialize(self, serialized):
        decoded = serialized.decode(self._encoding)
        return json.loads(decoded)
