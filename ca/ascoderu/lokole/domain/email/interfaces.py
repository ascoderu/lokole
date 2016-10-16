from abc import ABCMeta
from abc import abstractmethod


class EmailStore(metaclass=ABCMeta):
    @abstractmethod
    def create(self, *emails):
        """
        :type emails: list[dict]

        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def inbox(self, email_address):
        """
        :type email_address: str
        :rtype: collections.Iterable[dict]

        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def outbox(self, email_address):
        """
        :type email_address: str
        :rtype: collections.Iterable[dict]

        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def sent(self, email_address):
        """
        :type email_address: str
        :rtype: collections.Iterable[dict]

        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def search(self, email_address, query):
        """
        :type email_address: str
        :type query: str | None
        :rtype: collections.Iterable[dict]

        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def pending(self):
        """
        :rtype: collections.Iterable[dict]

        """
        raise NotImplementedError  # pragma: no cover


class AttachmentEncoder(metaclass=ABCMeta):
    @abstractmethod
    def encode(self, content):
        """
        :type content: bytes
        :rtype: str

        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def decode(self, encoded):
        """
        :type encoded: str
        :rtype: bytes

        """
        raise NotImplementedError  # pragma: no cover
