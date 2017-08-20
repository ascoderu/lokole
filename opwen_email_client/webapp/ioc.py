from logging import Formatter
from logging import StreamHandler

from flask import Flask
from flask_babel import Babel

from opwen_email_client.domain.email.attachment import Base64AttachmentEncoder as AttachmentEncoder  # noqa
from opwen_email_client.domain.email.client import HttpEmailServerClient as EmailServerClient  # noqa
from opwen_email_client.domain.email.sql_store import SqliteEmailStore as EmailStore  # noqa
from opwen_email_client.domain.email.sync import AzureSync as Sync  # noqa
from opwen_email_client.util.serialization import JsonSerializer as Serializer  # noqa
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.session import AttachmentsStore


if AppConfig.TESTING:
    from opwen_email_client.domain.email.client import LocalEmailServerClient as EmailServerClient  # noqa
    from opwen_email_client.domain.email.sync import LocalAzureSync as Sync  # noqa


class Ioc(object):
    serializer = Serializer()

    email_server_client = EmailServerClient(
        read_api=AppConfig.EMAIL_SERVER_READ_API_HOSTNAME,
        write_api=AppConfig.EMAIL_SERVER_WRITE_API_HOSTNAME,
        client_id=AppConfig.CLIENT_ID)

    email_store = EmailStore(
        database_path=AppConfig.LOCAL_EMAIL_STORE)

    email_sync = Sync(
        account_name=AppConfig.STORAGE_ACCOUNT_NAME,
        account_key=AppConfig.STORAGE_ACCOUNT_KEY,
        email_server_client=email_server_client,
        container=AppConfig.STORAGE_CONTAINER,
        serializer=serializer)

    attachment_encoder = AttachmentEncoder()

    attachments_session = AttachmentsStore(
        email_store=email_store,
        attachment_encoder=attachment_encoder)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(AppConfig)
    app.ioc = Ioc()

    handler = StreamHandler()
    handler.setFormatter(Formatter(AppConfig.LOG_FORMAT))
    app.logger.addHandler(handler)
    app.logger.setLevel(AppConfig.LOG_LEVEL)

    app.babel = Babel(app)

    return app
