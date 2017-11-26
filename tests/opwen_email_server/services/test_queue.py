from collections import namedtuple
from unittest import TestCase
from unittest.mock import MagicMock

from opwen_email_server.services.queue import AzureQueue


AzureQueueMessage = namedtuple(
    'Message',
    'id pop_receipt content dequeue_count')


class AzureQueueTests(TestCase):
    def test_enqueue_stores_message(self):
        queue, client_mock = self._given_queue()

        queue.enqueue({'foo': 'bar'})

        self.assertEqual(client_mock.put_message.call_count, 1)

    def test_creates_queue_only_once(self):
        queue, client_mock = self._given_queue()

        queue.enqueue({'foo': 'bar'})
        queue.enqueue({'foo': 'bar'})

        self.assertEqual(client_mock.create_queue.call_count, 1)

    def test_dequeue_removes_messages(self):
        queue, client_mock = self._given_queue(['{"foo":"bar"}'])

        messages = list(queue.dequeue())

        self.assertEqual(client_mock.get_messages.call_count, 1)
        self.assertEqual(client_mock.delete_message.call_count, 1)
        self.assertEqual(messages, [{'foo': 'bar'}])

    def test_batch_dequeue_removes_many_messages(self):
        queue, client_mock = self._given_queue(['{"foo":"bar"}', '{"baz":1}'])

        messages = list(queue.dequeue(batch=2))

        self.assertEqual(client_mock.get_messages.call_count, 1)
        self.assertEqual(client_mock.delete_message.call_count, 2)
        self.assertEqual(messages, [{'foo': 'bar'}, {'baz': 1}])

    def test_dequeue_with_exception_does_not_remove_message(self):
        queue, client_mock = self._given_queue(['{"foo":"bar"}'])

        messages = queue.dequeue()
        with self.assertRaises(Exception):
            _consume_and_throw(messages)

        self.assertEqual(client_mock.get_messages.call_count, 1)
        self.assertEqual(client_mock.delete_message.call_count, 0)

    def test_dequeue_rejects_unparsable_messages(self):
        queue, client_mock = self._given_queue(['{"corrupt'])

        messages = list(queue.dequeue())

        self.assertEqual(client_mock.get_messages.call_count, 1)
        self.assertEqual(client_mock.delete_message.call_count, 1)
        self.assertEqual(messages, [])

    # noinspection PyTypeChecker
    @classmethod
    def _given_queue(cls, messages=None, dequeue_count=0):
        client_mock = MagicMock()
        queue = AzureQueue(account='account', key='key', name='name',
                           factory=lambda *args, **kwargs: client_mock)

        if messages:
            client_mock.get_messages.return_value = [
                AzureQueueMessage(id=i, pop_receipt=i, content=message,
                                  dequeue_count=dequeue_count)
                for (i, message) in enumerate(messages)]

        return queue, client_mock


def _consume_and_throw(iterable):
    for _ in iterable:
        raise ValueError
