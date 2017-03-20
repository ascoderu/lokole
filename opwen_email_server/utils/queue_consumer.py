from time import sleep
from typing import Callable
from typing import Iterable


class QueueConsumer(object):
    def __init__(self, dequeue: Callable[[], Iterable[dict]],
                 poll_seconds: float=10) -> None:

        self._dequeue = dequeue
        self._poll_seconds = poll_seconds
        self._is_running = True

    def _process_message(self, message: dict):
        raise NotImplementedError

    def _run_once(self):
        messages = self._dequeue()
        for message in messages:
            self._process_message(message)

    def run_forever(self):
        while self._is_running:
            # noinspection PyBroadException
            try:
                self._run_once()
            except Exception:
                pass
            sleep(self._poll_seconds)
