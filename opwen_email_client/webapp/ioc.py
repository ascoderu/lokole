from flask import Flask
from flask_babelex import Babel

from opwen_email_client.domain.email.client import HttpEmailServerClient as EmailServerClient  # noqa
from opwen_email_client.domain.email.sql_store import SqliteEmailStore as EmailStore  # noqa
from opwen_email_client.domain.email.sync import AzureSync as Sync  # noqa
from opwen_email_client.util.serialization import JsonSerializer as Serializer  # noqa
from opwen_email_client.webapp.cache import cache
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.mkwvconf import blueprint as mkwvconf

if AppConfig.TESTING:
    from opwen_email_client.domain.email.client import LocalEmailServerClient as EmailServerClient  # noqa


class Ioc(object):
    serializer = Serializer()

    email_server_client = EmailServerClient(
        compression=AppConfig.COMPRESSION,
        hostname=AppConfig.EMAIL_SERVER_HOSTNAME,
        client_id=AppConfig.CLIENT_ID)

    email_store = EmailStore(
        restricted={AppConfig.NEWS_INBOX: AppConfig.NEWS_SENDERS},
        database_path=AppConfig.LOCAL_EMAIL_STORE)

    email_sync = Sync(
        compression=AppConfig.COMPRESSION,
        account_name=AppConfig.STORAGE_ACCOUNT_NAME,
        account_key=AppConfig.STORAGE_ACCOUNT_KEY,
        email_server_client=email_server_client,
        container=AppConfig.STORAGE_CONTAINER,
        provider=AppConfig.STORAGE_PROVIDER,
        serializer=serializer)


def create_app(config=AppConfig) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)

    app.babel = Babel(app)

    cache.init_app(app)

    app.register_blueprint(mkwvconf, url_prefix='/api/mkwvconf')

    return app
