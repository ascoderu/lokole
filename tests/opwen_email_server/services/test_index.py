from unittest import TestCase
from unittest.mock import Mock

from opwen_email_server.services.index import AzureIndex


class AzureIndexTests(TestCase):
    def test_inserts_all_values_into_all_tables(self):
        index, client_mock, batch_mock = self._given_index(
            {'table1': lambda _: [_['col1']],
             'table2': lambda _: _.get('col2', '')})

        index.insert('id1', {'col1': 'val1_1', 'col2': 'ab'})
        index.insert('id2', {'col1': 'val2_1', 'col2': '12'})
        index.insert('id3', {'col1': 'val2_1'})

        self.assertEqual(batch_mock.insert_or_replace_entity.call_count, 7)
        self.assertEqual(client_mock.commit_batch.call_count, 5)
        self.assertEqual(client_mock.create_table.call_count, 2)

    # noinspection PyTypeChecker
    @classmethod
    def _given_index(cls, tables):
        client_mock = Mock()
        batch_mock = Mock()
        index = AzureIndex(account='account', key='key', tables=tables,
                           client_factory=lambda *args, **kwargs: client_mock,
                           batch_factory=lambda *args, **kwargs: batch_mock)
        return index, client_mock, batch_mock
