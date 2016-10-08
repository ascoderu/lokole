from abc import ABCMeta
from abc import abstractmethod


class EmailStore(metaclass=ABCMeta):
    @abstractmethod
    def create(self, *emails):
        """
        :type emails: list[dict]

        """
        raise NotImplementedError

    @abstractmethod
    def inbox(self, email_address):
        """
        :type email_address: str
        :rtype: collections.Iterable[dict]

        """
        raise NotImplementedError

    @abstractmethod
    def outbox(self, email_address):
        """
        :type email_address: str
        :rtype: collections.Iterable[dict]

        """
        raise NotImplementedError

    @abstractmethod
    def sent(self, email_address):
        """
        :type email_address: str
        :rtype: collections.Iterable[dict]

        """
        raise NotImplementedError

    @abstractmethod
    def search(self, email_address, query):
        """
        :type email_address: str
        :type query: str
        :rtype: collections.Iterable[dict]

        """
        raise NotImplementedError

    @abstractmethod
    def pending(self):
        """
        :rtype: collections.Iterable[dict]

        """
        raise NotImplementedError


class AttachmentEncoder(metaclass=ABCMeta):
    @abstractmethod
    def encode(self, content):
        """
        :type content: bytes
        :rtype: str

        """
        raise NotImplementedError

    @abstractmethod
    def decode(self, encoded):
        """
        :type encoded: str
        :rtype: bytes

        """
        raise NotImplementedError
