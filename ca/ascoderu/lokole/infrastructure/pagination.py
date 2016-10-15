from itertools import islice


class Pagination(object):
    def __init__(self, items, page, page_size):
        """
        :type items: collections.Iterable[T]
        :type page: int
        :type page_size: int

        """
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
    def has_prevpage(self):
        """
        :rtype: bool

        """
        return self.page != 1

    @property
    def has_nextpage(self):
        """
        :rtype: bool

        """
        return len(self._items) == self.page_size
