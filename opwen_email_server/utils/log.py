from logging import Formatter
from logging import Handler
from logging import Logger
from logging import StreamHandler
from logging import getLogger
from typing import Any
from typing import Iterable
from typing import Optional

from applicationinsights import TelemetryClient
from applicationinsights.channel import TelemetryChannel
from applicationinsights.logging import LoggingHandler
from cached_property import cached_property

from opwen_email_server.config import APPINSIGHTS_KEY
from opwen_email_server.config import LOG_LEVEL
from opwen_email_server.constants.logging import SEPARATOR
from opwen_email_server.constants.logging import STDERR
from opwen_email_server.constants.logging import TELEMETRY_QUEUE_ITEMS
from opwen_email_server.constants.logging import TELEMETRY_QUEUE_SECONDS


class LogMixin(object):
    __logger = None  # type: Optional[Logger]
    __telemetry_channel = None  # type: Optional[TelemetryChannel]

    @classmethod
    def inject(cls, logger: Logger, channel: TelemetryChannel):
        logger.setLevel(LOG_LEVEL)
        cls.__logger = logger
        cls.__telemetry_channel = channel

    @classmethod
    def _default_log_handlers(cls) -> Iterable[Handler]:
        handlers = []

        stderr = StreamHandler()
        stderr.setFormatter(Formatter(STDERR))
        handlers.append(stderr)

        if APPINSIGHTS_KEY:
            appinsights = LoggingHandler(APPINSIGHTS_KEY)
            handlers.append(appinsights)

        return handlers

    @classmethod
    def _default_logger(cls) -> Logger:
        log = getLogger()
        for handler in cls._default_log_handlers():
            log.addHandler(handler)
        log.setLevel(LOG_LEVEL)
        return log

    @cached_property
    def _telemetry_client(self) -> Optional[TelemetryClient]:
        if not APPINSIGHTS_KEY:
            return None

        telemetry_client = TelemetryClient(
            APPINSIGHTS_KEY, self.__telemetry_channel)
        telemetry_client.channel.sender.send_interval_in_milliseconds = \
            TELEMETRY_QUEUE_SECONDS * 1000
        telemetry_client.channel.sender.max_queue_item_count = \
            TELEMETRY_QUEUE_ITEMS

        return telemetry_client

    @cached_property
    def _logger(self) -> Logger:
        return self.__logger or self._default_logger()

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

    def log_event(self, event_name: str, properties: Optional[dict] = None):
        self.log_info('%s%s%s', event_name, SEPARATOR, properties)

        if self._telemetry_client:
            self._telemetry_client.track_event(event_name, properties)
            self._telemetry_client.flush()
