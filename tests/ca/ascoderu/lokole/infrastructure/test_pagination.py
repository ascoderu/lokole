from unittest import TestCase

from ca.ascoderu.lokole.infrastructure.pagination import Pagination


class PaginationTests(TestCase):
    def test_page_should_be_nonzero(self):
        with self.assertRaises(ValueError):
            Pagination([1, 2, 3], page=0, page_size=1)

    def test_has_prevpage_on_first_page(self):
        pagination = Pagination([1, 2, 3], page=1, page_size=1)
        self.assertFalse(pagination.has_prevpage)

    def test_has_prevpage(self):
        pagination = Pagination([1, 2, 3], page=2, page_size=1)
        self.assertTrue(pagination.has_prevpage)

    def test_has_nextpage(self):
        pagination = Pagination([1, 2, 3], page=3, page_size=1)
        self.assertTrue(pagination.has_nextpage)

    def test_has_nextpage_on_last_page(self):
        pagination = Pagination([1, 2, 3], page=4, page_size=1)
        self.assertFalse(pagination.has_nextpage)

    def test_iter(self):
        pagination = Pagination([1, 2, 3], page=1, page_size=2)
        self.assertEqual(list(pagination), [1, 2])

    def test_iter_last(self):
        pagination = Pagination([1, 2, 3], page=2, page_size=2)
        self.assertEqual(list(pagination), [3])
