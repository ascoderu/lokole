from unittest import TestCase

from utils.pagination import paginate


class TestPaginate(TestCase):
    @classmethod
    def _do_paginate(cls, items, page, items_per_page):
        return paginate(items, page, items_per_page, error_out=False).items

    def test_returns_all_items_when_list_is_small(self):
        actual = self._do_paginate([1, 2, 3], page=1, items_per_page=10)
        self.assertListEqual(actual, [1, 2, 3])

    def test_returns_page(self):
        actual = self._do_paginate([1, 2, 3], page=2, items_per_page=1)
        self.assertListEqual(actual, [2])

    def test_returns_remaining_items_on_last_page(self):
        actual = self._do_paginate([1, 2, 3, 4], page=2, items_per_page=3)
        self.assertListEqual(actual, [4])

    def test_returns_empty_list_for_bad_page(self):
        actual = self._do_paginate([1, 2, 3], page=-1, items_per_page=10)
        self.assertListEqual(actual, [])

    def test_returns_empty_list_for_bad_items_per_page(self):
        actual = self._do_paginate([1, 2, 3], page=1, items_per_page=-1)
        self.assertListEqual(actual, [])

    def test_returns_empty_list_for_out_of_bounds_page(self):
        actual = self._do_paginate([1, 2, 3], page=100, items_per_page=10)
        self.assertListEqual(actual, [])
