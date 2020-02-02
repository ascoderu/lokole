from contextlib import contextmanager
from importlib import reload
from os import environ
from re import match
from unittest import TestCase

from opwen_email_server import config


class ConfigTests(TestCase):
    def test_queue_broker(self):
        envs = {
            'LOKOLE_QUEUE_BROKER_URL': 'foo://bar',
        }
        with setenvs(envs):
            self.assertEqual(config.QUEUE_BROKER, 'foo://bar')

    def test_queue_broker_servicebus(self):
        envs = {
            'LOKOLE_QUEUE_BROKER_SCHEME': 'azureservicebus',
            'LOKOLE_EMAIL_SERVER_QUEUES_SAS_NAME': 'user',
            'LOKOLE_EMAIL_SERVER_QUEUES_SAS_KEY': 'pass',
            'LOKOLE_EMAIL_SERVER_QUEUES_NAMESPACE': 'host',
        }
        with setenvs(envs):
            self.assertEqual(config.QUEUE_BROKER, 'azureservicebus://user:pass@host')

    def test_queue_broker_servicebus_urlsafe(self):
        envs = {
            'LOKOLE_QUEUE_BROKER_SCHEME': 'azureservicebus',
            'LOKOLE_EMAIL_SERVER_QUEUES_SAS_NAME': 'us/er',
            'LOKOLE_EMAIL_SERVER_QUEUES_SAS_KEY': 'pass',
            'LOKOLE_EMAIL_SERVER_QUEUES_NAMESPACE': 'host',
        }
        with setenvs(envs):
            self.assertEqual(config.QUEUE_BROKER, 'azureservicebus://us%2Fer:pass@host')

    def test_container_names_are_valid(self):
        acceptable_container_name = '^[a-z0-9][a-z0-9-]{2,62}$'

        for constant, value in get_constants(config):
            if constant.startswith('CONTAINER_') and not match(acceptable_container_name, value):
                self.fail(f'config {constant} is invalid: {value}, ' f'should be {acceptable_container_name}')


def get_constants(container):
    for variable_name in dir(container):
        if variable_name.upper() != variable_name:
            continue
        value = getattr(container, variable_name)
        if not isinstance(value, str):
            continue
        yield variable_name, value


@contextmanager
def setenvs(envs):
    for key, value in envs.items():
        environ[key] = value

    reload(config)
    yield

    for key in envs:
        del environ[key]
