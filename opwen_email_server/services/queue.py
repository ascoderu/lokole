from azure.servicebus import Message
from azure.servicebus import ServiceBusService
from typing import Callable

from opwen_email_server.utils.log import LogMixin
from opwen_email_server.utils.serialization import to_json


class AzureQueue(LogMixin):
    _max_message_retries = 5

    def __init__(self, name: str, namespace: str, sas_name: str, sas_key: str,
                 client: ServiceBusService=None,
                 factory: Callable[..., ServiceBusService]=ServiceBusService) \
            -> None:

        self._name = name
        self._namespace = namespace
        self._sas_name = sas_name
        self._sas_key = sas_key
        self.__client = client
        self._client_factory = factory

    @property
    def _client(self) -> ServiceBusService:
        if self.__client is not None:
            return self.__client
        client = self._client_factory(
            service_namespace=self._namespace,
            shared_access_key_name=self._sas_name,
            shared_access_key_value=self._sas_key)
        self.__client = client
        return client

    @property
    def name(self) -> str:
        return self._name

    @classmethod
    def _pack(cls, content: dict) -> Message:
        body = to_json(content).encode('utf-8')
        return Message(body)

    def enqueue(self, content: dict):
        message = self._pack(content)
        self._client.send_queue_message(self._name, message)
        self.log_debug('sent message')

    def extra_log_args(self):
        yield 'queue %s', self._name
