from unittest import TestCase

from opwen_email_server.utils import unique


class NewEmailIdTests(TestCase):
    def test_unique(self):
        id1 = unique.new_email_id({'from': 'foo'})
        id2 = unique.new_email_id({'from': 'bar'})
        id3 = unique.new_email_id({'from': 'foo'})

        self.assertNotEqual(id1, id2)
        self.assertNotEqual(id2, id3)
        self.assertEqual(id1, id3)


class NewGuidTests(TestCase):
    def test_is_unique(self):
        new_client_id = unique.NewGuid()

        id1 = new_client_id()
        id2 = new_client_id()

        self.assertNotEqual(id1, id2)

    def test_is_repeatable(self):
        new_client_id_1 = unique.NewGuid(1)
        new_client_id_2 = unique.NewGuid(1)

        id1 = new_client_id_1()
        id2 = new_client_id_2()
        id3 = new_client_id_2()

        self.assertEqual(id1, id2)
        self.assertNotEqual(id2, id3)
