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

        self.assertEqual(client_mock.insert_or_replace_entity.call_count, 7)
        self.assertEqual(client_mock.create_table.call_count, 2)

    def test_sanitizes_forbidden_values(self):
        index, client_mock, batch_mock = self._given_index(
            {'table1': lambda _: [_['col1']]})

        index.insert('id1', {'col1': 'san?\\#\nit\t\rized'})

        client_mock.insert_or_replace_entity.assert_called_once_with(
            'table1', {'RowKey': 'id1', 'PartitionKey': 'sanitized'})

    def test_shortens_long_values(self):
        index, client_mock, batch_mock = self._given_index(
            {'table1': lambda _: [_['col1']]})
        index.insert('id1', {'col1': 'very long' * 1024})

        call_args = client_mock.insert_or_replace_entity.call_args[0]
        self.assertEqual(call_args[0], 'table1')
        self.assertLessEqual(len(call_args[1]['PartitionKey']), 1000)

    def test_delete(self):
        index, client_mock, batch_mock = self._given_index(
            {'table1': lambda _: [_['col1']]})

        index.delete('table1', 'col1', ['id1'])

        self.assertEqual(batch_mock.delete_entity.call_count, 1)
        self.assertEqual(client_mock.commit_batch.call_count, 1)

    def test_query(self):
        items = [{'PartitionKey': 'col1', 'RowKey': 'id1234'}]
        index, client_mock, batch_mock = self._given_index(
            {'table1': lambda _: [_['col1']]}, items)

        queried = list(index.query('table1', 'col1'))

        self.assertEqual(client_mock.query_entities.call_count, 1)
        self.assertEqual(queried, ['id1234'])

    # noinspection PyTypeChecker
    @classmethod
    def _given_index(cls, tables, items=None):
        client_mock = Mock()
        batch_mock = Mock()
        index = AzureIndex(account='account', key='key', tables=tables,
                           client_factory=lambda *args, **kwargs: client_mock,
                           batch_factory=lambda *args, **kwargs: batch_mock)

        if items:
            client_mock.query_entities.return_value = items

        return index, client_mock, batch_mock
