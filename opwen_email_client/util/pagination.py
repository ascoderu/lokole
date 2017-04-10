from itertools import islice
from typing import Iterable
from typing import TypeVar

T = TypeVar('T')


class Pagination(object):
    def __init__(self, items: Iterable[T], page: int, page_size: int):
        if page < 1:
            raise ValueError('page must be greater than or equal to 1')

        start = (page - 1) * page_size
        stop = page * page_size
        self._items = list(islice(items, start, stop))
        self.page = page
        self.page_size = page_size

    def __iter__(self):
        return iter(self._items)

    @property
    def has_prevpage(self) -> bool:
        return self.page != 1

    @property
    def has_nextpage(self) -> bool:
        return len(self._items) == self.page_size
