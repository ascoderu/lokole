from time import sleep
from typing import Callable
from typing import Iterable

from opwen_email_server.azure_constants import QUEUE_POLL_INTERVAL
from opwen_email_server.utils.log import LogMixin


class QueueConsumer(LogMixin):
    def __init__(self, dequeue: Callable[[], Iterable[dict]],
                 poll_seconds: float=QUEUE_POLL_INTERVAL) -> None:

        self._dequeue = dequeue
        self._poll_seconds = poll_seconds
        self._is_running = True

    def _process_message(self, message: dict):
        raise NotImplementedError

    def run_once(self):
        messages = self._dequeue()
        for message in messages:
            self._process_message(message)

    def run_forever(self):
        self.log_debug('queue consumer listening')
        while self._is_running:
            self.log_debug('starting polling queue')
            # noinspection PyBroadException
            try:
                self.run_once()
            except Exception:
                self.log_exception('error polling queue')
                pass
            self.log_debug('done polling queue')
            sleep(self._poll_seconds)
