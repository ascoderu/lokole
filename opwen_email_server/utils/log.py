from logging import Formatter
from logging import Handler
from logging import Logger
from logging import StreamHandler
from logging import getLogger
from typing import Any
from typing import Iterable
from typing import Optional

from applicationinsights import TelemetryClient
from applicationinsights import exceptions

from opwen_email_server.config import APPINSIGHTS_KEY
from opwen_email_server.config import LOG_LEVEL
from opwen_email_server.constants.logging import SEPARATOR
from opwen_email_server.constants.logging import STDERR
from opwen_email_server.constants.logging import TELEMETRY_QUEUE_ITEMS
from opwen_email_server.constants.logging import TELEMETRY_QUEUE_SECONDS
from opwen_email_server.utils.collections import singleton


@singleton
def _get_log_handlers() -> Iterable[Handler]:
    stderr = StreamHandler()
    stderr.setFormatter(Formatter(STDERR))
    return [stderr]


@singleton
def _get_logger() -> Logger:
    log = getLogger()
    for handler in _get_log_handlers():
        log.addHandler(handler)
    log.setLevel(LOG_LEVEL)
    return log


@singleton
def _get_telemetry_client() -> Optional[TelemetryClient]:
    if not APPINSIGHTS_KEY:
        return None

    telemetry_client = TelemetryClient(APPINSIGHTS_KEY)
    telemetry_client.channel.sender.send_interval_in_milliseconds = \
        TELEMETRY_QUEUE_SECONDS * 1000
    telemetry_client.channel.sender.max_queue_item_count = \
        TELEMETRY_QUEUE_ITEMS
    exceptions.enable(APPINSIGHTS_KEY)

    return telemetry_client


class LogMixin(object):
    _logger = _get_logger()
    _telemetry_client = _get_telemetry_client()

    def log_debug(self, message: str, *args: Any):
        self._log('debug', message, args)

    def log_info(self, message: str, *args: Any):
        self._log('info', message, args)

    def log_warning(self, message: str, *args: Any):
        self._log('warning', message, args)

    def log_exception(self, message: str, *args: Any):
        self._log('exception', message, args)

    def _log(self, level: str, log_message: str, log_args: Iterable[Any]):
        message_parts = ['%s']
        args = [self.__class__.__name__]
        message_parts.append(log_message)
        args.extend(log_args)
        message = SEPARATOR.join(message_parts)
        log = getattr(self._logger, level)
        log(message, *args)

        if self._telemetry_client:
            self._telemetry_client.track_trace(
                message % tuple(args), {'level': level})

            if self.should_send_message_immediately(level):
                self._telemetry_client.flush()

    # noinspection PyMethodMayBeStatic
    def log_event(self, event_name: str, properties: Optional[dict] = None):
        self._logger.info('%s%s%s', event_name, SEPARATOR, properties)

        if self._telemetry_client:
            self._telemetry_client.track_event(event_name, properties)
            self._telemetry_client.flush()

    # noinspection PyMethodMayBeStatic
    def should_send_message_immediately(self, level: str) -> bool:
        return level != 'debug'
