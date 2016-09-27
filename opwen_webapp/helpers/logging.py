from logging import Filter
from logging import Formatter
from logging.handlers import RotatingFileHandler

from flask_login import current_user


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


def create_logging_handler(app):
    """
    :type app: flask.Flask

    """
    handler = RotatingFileHandler(
        filename=app.config['LOG_FILE'],
        maxBytes=app.config['LOG_MAX_BYTES'],
        backupCount=app.config['LOG_NUM_ROTATES'])

    handler.addFilter(InjectCurrentUserName())
    handler.setLevel(app.config['LOG_LEVEL'])
    handler.setFormatter(Formatter(app.config['LOG_FORMAT']))

    app.logger.addHandler(handler)


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
