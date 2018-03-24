from contextlib import contextmanager
from unittest import TestCase

from opwen_email_server.services.queue_consumer import QueueConsumer


class TestQueueConsumer(QueueConsumer):
    def __init__(self, message_processor, message_generator, max_runs):
        super().__init__(message_generator, poll_seconds=0.01)
        self.messages_processed = 0
        self.times_waited = 0
        self.exceptions_encountered = 0
        self._num_runs = 0
        self._max_runs = max_runs
        self._message_processor = message_processor

    def _process_message(self, message: dict):
        self._message_processor()

    def _track_run(self):
        self._num_runs += 1
        if self._num_runs >= self._max_runs:
            self._is_running = False

    def _report_success(self):
        self._track_run()
        self.messages_processed += 1

    def _report_error(self, ex: Exception):
        self._track_run()
        self.exceptions_encountered += 1

    def _wait_for_next_message(self):
        self._track_run()
        self.times_waited += 1


class QueueConsumerTests(TestCase):
    def test_processes_messages_immediately_if_there_is_more_work(self):
        def _process(): pass

        @contextmanager
        def _produce(): yield [{"foo": "bar"}]

        consumer = TestQueueConsumer(_process, _produce, max_runs=10)

        consumer.run_forever()

        self.assertEqual(consumer.messages_processed, 10)
        self.assertEqual(consumer.times_waited, 0)

    def test_waits_for_new_messages_if_there_is_no_work_to_do(self):
        def _process(): pass

        @contextmanager
        def _produce(): yield []

        consumer = TestQueueConsumer(_process, _produce, max_runs=10)

        consumer.run_forever()

        self.assertEqual(consumer.messages_processed, 0)
        self.assertEqual(consumer.times_waited, 10)

    def test_waits_or_processes_messages_if_available(self):
        self.messages_produced = 0

        def _process(): pass

        @contextmanager
        def _produce():
            if self.messages_produced % 2 == 0:
                yield []
            else:
                yield [{"foo": "bar"}]
            self.messages_produced += 1

        consumer = TestQueueConsumer(_process, _produce, max_runs=10)

        consumer.run_forever()

        self.assertEqual(consumer.messages_processed, 5)
        self.assertEqual(consumer.times_waited, 5)

    def test_ignores_exceptions_while_running(self):
        def _throw(): raise ValueError

        @contextmanager
        def _produce(): yield [{"foo": "bar"}]

        consumer = TestQueueConsumer(_throw, _produce, max_runs=10)

        consumer.run_forever()

        self.assertEqual(consumer.exceptions_encountered, 10)
