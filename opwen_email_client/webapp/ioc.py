from flask import Flask
from flask_babelex import Babel

from opwen_email_client.domain.email.client import HttpEmailServerClient as EmailServerClient  # noqa
from opwen_email_client.domain.email.sql_store import SqliteEmailStore as EmailStore  # noqa
from opwen_email_client.domain.email.sync import AzureSync as Sync  # noqa
from opwen_email_client.util.serialization import JsonSerializer as Serializer  # noqa
from opwen_email_client.webapp.cache import cache
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.forms.login import LoginForm
from opwen_email_client.webapp.forms.login import RegisterForm
from opwen_email_client.webapp.login import FlaskLoginUserStore as UserStore
from opwen_email_client.webapp.mkwvconf import blueprint as mkwvconf
from opwen_email_client.webapp.security import security

if AppConfig.TESTING:
    from opwen_email_client.domain.email.client import LocalEmailServerClient as EmailServerClient  # noqa


class Ioc:
    def __init__(self):
        self.serializer = Serializer()

        self.email_server_client = EmailServerClient(
            compression=AppConfig.COMPRESSION,
            hostname=AppConfig.EMAIL_SERVER_HOSTNAME,
            client_id=AppConfig.CLIENT_ID,
        )

        self.email_store = EmailStore(
            page_size=AppConfig.EMAILS_PER_PAGE,
            restricted={AppConfig.NEWS_INBOX: AppConfig.NEWS_SENDERS},
            database_path=AppConfig.LOCAL_EMAIL_STORE,
        )

        self.email_sync = Sync(
            compression=AppConfig.COMPRESSION,
            account_name=AppConfig.STORAGE_ACCOUNT_NAME,
            account_key=AppConfig.STORAGE_ACCOUNT_KEY,
            email_server_client=self.email_server_client,
            container=AppConfig.STORAGE_CONTAINER,
            provider=AppConfig.STORAGE_PROVIDER,
            serializer=self.serializer,
        )

        self.user_store = UserStore()


def create_app(config=AppConfig) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)

    app.babel = Babel(app)

    app.ioc = Ioc()

    cache.init_app(app)
    app.ioc.user_store.init_app(app)
    security.init_app(app, app.ioc.user_store.datastore, register_form=RegisterForm, login_form=LoginForm)

    app.register_blueprint(mkwvconf, url_prefix='/api/mkwvconf')

    return app
