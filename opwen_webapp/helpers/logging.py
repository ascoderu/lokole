from logging import Filter
from logging import Formatter
from logging.handlers import RotatingFileHandler

from flask_login import current_user

from config import Config


class InjectCurrentUserName(Filter):
    def filter(self, record):
        record.username = self._username
        return True

    @property
    def _username(self):
        """
        :rtype: str

        """
        if not current_user:
            return '(None)'
        if not current_user.is_authenticated:
            return '(Anon)'
        return current_user.name


def create_logging_handler():
    """
    :rtype: logging.Handler

    """
    handler = RotatingFileHandler(
        filename=Config.LOG_FILE,
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_NUM_ROTATES)

    handler.addFilter(InjectCurrentUserName())
    handler.setLevel(Config.LOG_LEVEL)
    handler.setFormatter(Formatter(Config.LOG_FORMAT))

    return handler


def exception_to_logline(exception, newline='<br>'):
    """
    :type exception: str
    :type newline: str
    :rtype: str

    """
    exception = exception.splitlines()
    exception = (line.replace('\t', ' ') for line in exception)
    exception = (line.strip() for line in exception)
    exception = newline.join(exception)
    return exception
