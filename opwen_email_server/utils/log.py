from logging import CRITICAL
from logging import DEBUG
from logging import Formatter
from logging import Handler
from logging import INFO
from logging import Logger
from logging import StreamHandler
from logging import WARNING
from logging import getLogger
from typing import Any
from typing import Iterable
from typing import Optional

from applicationinsights import TelemetryClient
from applicationinsights.logging import LoggingHandler
from cached_property import cached_property

from opwen_email_server.config import APPINSIGHTS_KEY
from opwen_email_server.config import LOG_LEVEL
from opwen_email_server.constants.logging import SEPARATOR
from opwen_email_server.constants.logging import STDERR
from opwen_email_server.constants.logging import TELEMETRY_QUEUE_ITEMS
from opwen_email_server.constants.logging import TELEMETRY_QUEUE_SECONDS
from opwen_email_server.utils.collections import append


class LogMixin(object):
    @classmethod
    def _default_log_handlers(cls) -> Iterable[Handler]:
        stderr = StreamHandler()
        stderr.setFormatter(Formatter(STDERR))
        yield stderr

        if APPINSIGHTS_KEY:
            yield LoggingHandler(APPINSIGHTS_KEY)

    @cached_property
    def _logger(self) -> Logger:
        log = getLogger()
        for handler in self._default_log_handlers():
            log.addHandler(handler)
        log.setLevel(LOG_LEVEL)
        return log

    @cached_property
    def _telemetry_client(self) -> Optional[TelemetryClient]:
        if not APPINSIGHTS_KEY:
            return None

        telemetry_client = TelemetryClient(APPINSIGHTS_KEY)
        telemetry_client.channel.sender.send_interval_in_milliseconds = \
            TELEMETRY_QUEUE_SECONDS * 1000
        telemetry_client.channel.sender.max_queue_item_count = \
            TELEMETRY_QUEUE_ITEMS

        return telemetry_client

    def log_debug(self, message: str, *args: Any):
        self._log(DEBUG, message, args)

    def log_info(self, message: str, *args: Any):
        self._log(INFO, message, args)

    def log_warning(self, message: str, *args: Any):
        self._log(WARNING, message, args)

    def log_exception(self, ex: Exception, message: str, *args: Any):
        self._log(CRITICAL, message + ' (%r)', append(args, ex))

        if self._telemetry_client:
            # noinspection PyBroadException
            try:
                raise ex
            except Exception:
                self._telemetry_client.track_exception()

    def _log(self, level: int, log_message: str, log_args: Iterable[Any]):
        if not self._logger.isEnabledFor(level):
            return

        message_parts = ['%s']
        args = [self.__class__.__name__]
        message_parts.append(log_message)
        args.extend(log_args)
        message = SEPARATOR.join(message_parts)
        self._logger.log(level, message, *args)

    def log_event(self, event_name: str, properties: Optional[dict] = None):
        self.log_info('%s%s%s', event_name, SEPARATOR, properties)

        if self._telemetry_client:
            self._telemetry_client.track_event(event_name, properties)
            self._telemetry_client.flush()
