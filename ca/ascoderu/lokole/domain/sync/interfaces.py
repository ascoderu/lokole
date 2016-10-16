from abc import ABCMeta
from abc import abstractmethod


class Sync(metaclass=ABCMeta):
    @abstractmethod
    def upload(self, items):
        """
        :type items: collections.Iterable[T]

        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def download(self):
        """
        :rtype: collections.Iterable[T]

        """
        raise NotImplementedError  # pragma: no cover
