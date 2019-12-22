from logging import CRITICAL
from logging import DEBUG
from logging import INFO
from logging import NOTSET
from logging import WARNING
from logging import Formatter
from logging import Handler
from logging import Logger
from logging import StreamHandler
from logging import getLogger
from typing import Any
from typing import Iterable
from typing import Optional

from applicationinsights import TelemetryClient
from applicationinsights.channel import AsynchronousQueue
from applicationinsights.channel import AsynchronousSender
from applicationinsights.channel import NullSender
from applicationinsights.channel import TelemetryChannel
from applicationinsights.logging import LoggingHandler
from cached_property import cached_property

from opwen_email_server.config import APPINSIGHTS_HOST
from opwen_email_server.config import APPINSIGHTS_KEY
from opwen_email_server.config import APPINSIGHTS_LOG_LEVEL
from opwen_email_server.config import LOG_LEVEL
from opwen_email_server.constants.logging import APPINSIGHTS
from opwen_email_server.constants.logging import STDERR
from opwen_email_server.utils.collections import append
from opwen_email_server.utils.collections import singleton


@singleton
def _create_telemetry_channel() -> TelemetryChannel:
    sender = AsynchronousSender(APPINSIGHTS_HOST) if APPINSIGHTS_HOST else NullSender()
    queue = AsynchronousQueue(sender)
    return TelemetryChannel(queue=queue)


class LogMixin:
    _telemetry_channel = _create_telemetry_channel()
    _telemetry_key = APPINSIGHTS_KEY or '00000000-0000-0000-0000-000000000000'

    @cached_property
    def _default_log_handlers(self) -> Iterable[Handler]:
        handlers = []

        stderr = StreamHandler()
        stderr.setFormatter(Formatter(STDERR))
        stderr.setLevel(LOG_LEVEL)
        handlers.append(stderr)

        appinsights = LoggingHandler(self._telemetry_key, telemetry_channel=self._telemetry_channel)
        appinsights.setFormatter(Formatter(APPINSIGHTS))
        appinsights.setLevel(APPINSIGHTS_LOG_LEVEL)
        handlers.append(appinsights)

        return handlers

    @cached_property
    def _logger(self) -> Logger:
        log = getLogger(self.__class__.__name__)
        log.setLevel(NOTSET)
        log.propagate = False
        for handler in self._default_log_handlers:
            log.addHandler(handler)
        return log

    @cached_property
    def _telemetry_client(self) -> TelemetryClient:
        return TelemetryClient(self._telemetry_key, self._telemetry_channel)

    def log_debug(self, message: str, *args: Any):
        self._log(DEBUG, message, args)

    def log_info(self, message: str, *args: Any):
        self._log(INFO, message, args)

    def log_warning(self, message: str, *args: Any):
        self._log(WARNING, message, args)

    def log_exception(self, ex: Exception, message: str, *args: Any):
        self._log(CRITICAL, message + ' (%r)', append(args, ex))

        # noinspection PyBroadException
        try:
            raise ex
        except Exception:
            self._telemetry_client.track_exception()
            self._telemetry_channel.flush()

    def _log(self, level: int, log_message: str, log_args: Iterable[Any]):
        self._logger.log(level, log_message, *log_args)

    def log_event(self, event_name: str, properties: Optional[dict] = None):
        self.log_info('%s|%s', event_name, properties)
        self._telemetry_client.track_event(event_name, properties)
