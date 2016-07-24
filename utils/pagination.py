from flask_sqlalchemy import Pagination
from werkzeug.exceptions import abort


class ListPagination(Pagination):
    def __init__(self, items, page, items_per_page, error_out=True):
        """
        :type items: list
        :type page: int
        :type items_per_page: int
        :type error_out: bool

        """
        page_items = self._get_page(items, page, items_per_page)
        if items and not page_items and error_out:
            abort(404)

        super().__init__(page=page, per_page=items_per_page, total=len(items),
                         items=page_items, query=None)

    @classmethod
    def _get_page(cls, items, page, items_per_page):
        """
        :type items: list
        :type page: int
        :type items_per_page: int

        """
        if items_per_page < 1 or page < 1:
            return []

        lower = max((page - 1) * items_per_page, 0)
        upper = min(page * items_per_page, len(items))
        return items[lower:upper]


def paginate(items, page, items_per_page, error_out=True):
    """
    :type items: collections.Iterable | flask_sqlalchemy.BaseQuery
    :type page: int
    :type items_per_page: int
    :type error_out: bool
    :rtype: Pagination

    """
    try:
        return items.paginate(page, items_per_page, error_out)
    except AttributeError:
        return ListPagination(list(items), page, items_per_page, error_out)
