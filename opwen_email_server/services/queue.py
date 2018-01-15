from contextlib import contextmanager
from json import loads

from azure.storage.queue import QueueService
from typing import Callable
from typing import Iterable

from opwen_email_server.utils.log import LogMixin
from opwen_email_server.utils.serialization import to_json


class AzureQueue(LogMixin):
    _max_message_retries = 5

    def __init__(self, account: str, key: str, name: str,
                 client: QueueService=None,
                 factory: Callable[..., QueueService]=QueueService) -> None:

        self._account = account
        self._key = key
        self._name = name
        self.__client = client
        self._client_factory = factory

    @property
    def _client(self) -> QueueService:
        if self.__client is not None:
            return self.__client
        client = self._client_factory(self._account, self._key)
        client.create_queue(self._name)
        self.__client = client
        return client

    @property
    def name(self) -> str:
        return self._name

    @classmethod
    def _pack(cls, content: dict) -> str:
        return to_json(content)

    @classmethod
    def _unpack(cls, message: str) -> dict:
        return loads(message)

    def enqueue(self, content: dict):
        message = self._pack(content)
        self._client.put_message(self._name, message)
        self.log_debug('received message')

    @contextmanager  # type: ignore
    def dequeue(self, lock_seconds: int=10) -> Iterable[dict]:
        messages = self._client.get_messages(self._name, 1, lock_seconds)
        messages = list(messages)
        if not messages:
            yield []  # type: ignore
        else:
            message = messages[0]
            delete_message = False

            # noinspection PyBroadException
            try:
                payload = self._unpack(message.content)
            except Exception:
                self.log_exception(
                    'error unpacking message %r, purging',
                    message.id)
                delete_message = True
                yield []  # type: ignore
            else:
                # noinspection PyBroadException
                try:
                    yield [payload]  # type: ignore
                except Exception as ex:
                    if message.dequeue_count > self._max_message_retries:
                        self.log_exception(
                            'too many retries for message %r, purging:%r',
                            message.id, ex)
                        delete_message = True
                    else:
                        self.log_exception(
                            'error processing message %r, retrying:%r',
                            message.id, ex)
                else:
                    self.log_debug(
                        'done with message %r, deleting',
                        message.id)
                    delete_message = True

            if delete_message:
                self._client.delete_message(self._name, message.id,
                                            message.pop_receipt)

    def extra_log_args(self):
        yield 'queue %s', self._name
