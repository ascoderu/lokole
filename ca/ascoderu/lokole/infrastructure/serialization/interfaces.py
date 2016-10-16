from abc import ABCMeta
from abc import abstractmethod


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
