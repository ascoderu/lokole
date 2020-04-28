from logging import getLogger

from opwen_email_client.webapp.ioc import create_app

app = create_app()

if __name__ != '__main__':
    gunicorn_logger = getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

from opwen_email_client.webapp import jinja  # noqa: F401,E402  # isort:skip
from opwen_email_client.webapp import login  # noqa: F401,E402  # isort:skip
from opwen_email_client.webapp import views  # noqa: F401,E402  # isort:skip
