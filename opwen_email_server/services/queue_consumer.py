from time import sleep
from typing import Callable
from typing import Iterable

from opwen_email_server.azure_constants import QUEUE_POLL_INTERVAL
from opwen_email_server.utils.log import LogMixin
from opwen_email_server.config import QUEUE_ERROR_FILE
from opwen_email_server.utils.temporary import remove_if_exists


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
            except Exception as ex:
                self._report_error(ex)
            else:
                self._report_success()
            sleep(self._poll_seconds)

    def _report_success(self):
        self.log_debug('done polling queue')

        if QUEUE_ERROR_FILE:
            remove_if_exists(QUEUE_ERROR_FILE)

    def _report_error(self, ex: Exception):
        self.log_exception('error polling queue')

        if QUEUE_ERROR_FILE:
            with open(QUEUE_ERROR_FILE, 'a') as fobj:
                fobj.write('{}\n'.format(ex))
