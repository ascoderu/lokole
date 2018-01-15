from time import sleep

from opwen_email_server.azure_constants import QUEUE_POLL_INTERVAL
from opwen_email_server.utils.log import LogMixin
from opwen_email_server.config import QUEUE_ERROR_FILE
from opwen_email_server.utils.temporary import remove_if_exists


class QueueConsumer(LogMixin):
    def __init__(self, dequeue,
                 poll_seconds: float=QUEUE_POLL_INTERVAL) -> None:

        self._dequeue = dequeue
        self._poll_seconds = poll_seconds
        self._is_running = True

    def _process_message(self, message: dict):
        raise NotImplementedError

    def run_once(self):
        with self._dequeue() as messages:
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
        self.log_exception('error polling queue:%r', ex)

        if QUEUE_ERROR_FILE:
            with open(QUEUE_ERROR_FILE, 'a') as fobj:
                fobj.write('{}\n'.format(ex))


def cli(job_class):
    from argparse import ArgumentParser
    from os.path import dirname
    from os.path import join

    parser = ArgumentParser()
    parser.add_argument('--once', action='store_true', default=False)
    args = parser.parse_args()

    try:
        # noinspection PyUnresolvedReferences
        from dotenv import load_dotenv
        load_dotenv(join(dirname(__file__), '.env'))
    except ImportError:
        pass

    job = job_class()
    if args.once:
        job.run_once()
    else:
        job.run_forever()
