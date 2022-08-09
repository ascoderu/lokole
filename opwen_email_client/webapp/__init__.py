from logging import getLogger

from flask import Flask
from flask_babelex import Babel

from opwen_email_client.webapp.cache import cache
from opwen_email_client.webapp.commands import managesbp
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.forms.login import RegisterForm
from opwen_email_client.webapp.ioc import _new_ioc
from opwen_email_client.webapp.mkwvconf import blueprint as mkwvconf
from opwen_email_client.webapp.security import security

app = Flask(__name__, static_url_path=AppConfig.APP_ROOT + '/static')
app.config.from_object(AppConfig)

app.babel = Babel(app)

app.ioc = _new_ioc(AppConfig.IOC)

cache.init_app(app)
app.ioc.user_store.init_app(app)
security.init_app(app, app.ioc.user_store.r, register_form=RegisterForm, login_form=app.ioc.login_form)

app.register_blueprint(mkwvconf, url_prefix=AppConfig.APP_ROOT + '/api/mkwvconf')
app.register_blueprint(managesbp)

if __name__ != '__main__':
    gunicorn_logger = getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

from opwen_email_client.webapp import jinja  # noqa: F401,E402  # isort:skip
from opwen_email_client.webapp import login  # noqa: F401,E402  # isort:skip
from opwen_email_client.webapp import views  # noqa: F401,E402  # isort:skip
