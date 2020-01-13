from os import getenv
from random import choice
from string import ascii_letters
from unittest import TestCase
from unittest import skipUnless

from cached_property import cached_property
from kombu import Connection
from kombu import Exchange
from kombu import Queue

from opwen_email_server.config import QUEUE_BROKER
from opwen_email_server.integration import celery as app  # ensure app tasks are loaded
from celery import current_app  # cerely's __init__.py


class TransportTests(TestCase):
    exchange_name = getenv('KOMBU_EXCHANGE', 'testexchange')
    queue_name = getenv('KOMBU_QUEUE', 'testqueue')
    routing_key = getenv('KOMBU_ROUTING_KEY', 'testkey')

    @cached_property
    def exchange(self) -> Exchange:
        return Exchange(self.exchange_name, 'direct', durable=True)

    @cached_property
    def queue(self) -> Queue:
        return Queue(self.queue_name, exchange=self.exchange, routing_key=self.routing_key)

    @skipUnless(QUEUE_BROKER, 'no celery broker configured')
    def test_send_message(self):
        random_message = ''.join(choice(ascii_letters)  # nosec
                                 for _ in range(30))

        with Connection(QUEUE_BROKER) as connection:
            producer = connection.Producer()
            producer.publish(
                {'message': random_message, 'test': True},
                exchange=self.exchange,
                routing_key=self.routing_key,
                declare=[self.queue],
            )

    def test_celery_task_routes(self):
        registered_celerey_tasks = [
            task_name for task_name in current_app.tasks.keys() if not task_name.startswith('celery.')
        ]

        for task_name in registered_celerey_tasks:
            self.assertIs(
                task_name in app.task_routes.keys(), True,
                "Function '" + task_name + "' not found in the task_routes dictionary in '" + app.__name__ + "' module")