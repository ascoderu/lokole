from abc import ABCMeta
from abc import abstractmethod
from typing import Iterable
from typing import List
from typing import TypeVar

T = TypeVar('T')


class UserStore(metaclass=ABCMeta):
    @abstractmethod
    def fetch_pending(self) -> List[T]:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def mark_as_synced(self, users: Iterable[T]) -> None:
        raise NotImplementedError  # pragma: no cover
