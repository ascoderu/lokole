from queue import Queue
from threading import Thread
from sys import exc_info
from time import sleep
from unittest import TestCase

from opwen_email_server.utils.queue_consumer import QueueConsumer


class TestQueueConsumer(QueueConsumer):
    def __init__(self, message_processor, message_generator):
        super().__init__(message_generator, poll_seconds=0.01)
        self.messages_processed = 0
        self._message_processor = message_processor

    def _process_message(self, message: dict):
        self._message_processor()
        self.messages_processed += 1


class ExceptionPreservingThread(Thread):
    def __init__(self, action):
        super().__init__()
        self._action = action
        self._exceptions = Queue()

    # noinspection PyBroadException
    def run(self):
        try:
            self._action()
        except Exception:
            self._exceptions.put(exc_info())
        self._exceptions.put(None)

    def join_with_exceptions(self):
        exception = self._exceptions.get()
        return exception


class QueueConsumerTests(TestCase):
    def test_processes_messages(self):
        consumer = TestQueueConsumer(lambda: None, lambda: [{"foo": "bar"}])

        self._when_running(consumer, 0.05)

        self.assertGreaterEqual(consumer.messages_processed, 5)

    def test_ignores_exceptions_while_running(self):
        def _throw(): raise ValueError
        consumer = TestQueueConsumer(_throw, lambda: [{"foo": "bar"}])

        exception = self._when_running(consumer, 0.01)

        self.assertIsNone(exception)

    @classmethod
    def _when_running(cls, consumer, time):
        thread = ExceptionPreservingThread(action=consumer.run_forever)
        thread.start()
        sleep(time)
        consumer._is_running = False
        return thread.join_with_exceptions()
