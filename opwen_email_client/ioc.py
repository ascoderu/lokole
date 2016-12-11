from logging import Formatter
from logging import StreamHandler

from flask import Flask
from flask_babel import Babel
from opwen_domain.email.base64 import Base64AttachmentEncoder
from opwen_domain.email.sqlite import SqliteEmailStore
from opwen_domain.sync.azure import AzureAuth
from opwen_domain.sync.azure import AzureSync
from opwen_infrastructure.serialization.json import JsonSerializer

from opwen_email_client.config import AppConfig
from opwen_email_client.session import AttachmentsStore


class Ioc(object):
    serializer = JsonSerializer()

    email_store = SqliteEmailStore(
        database_path=AppConfig.LOCAL_EMAIL_STORE,
        serializer=serializer)

    email_sync = AzureSync(
        auth=AzureAuth(
            account=AppConfig.STORAGE_ACCOUNT_NAME,
            key=AppConfig.STORAGE_ACCOUNT_KEY,
            container=AppConfig.STORAGE_CONTAINER),
        download_locations=[AppConfig.STORAGE_DOWNLOAD_PATH],
        upload_locations=[AppConfig.STORAGE_UPLOAD_PATH],
        serializer=serializer)

    attachment_encoder = Base64AttachmentEncoder()

    attachments_session = AttachmentsStore(
        email_store=email_store,
        attachment_encoder=attachment_encoder)


def create_app():
    """
    :rtype: flask.Flask

    """
    app = Flask(__name__)
    app.config.from_object(AppConfig)
    app.ioc = Ioc()

    logger = StreamHandler()
    logger.setFormatter(Formatter(AppConfig.LOG_FORMAT))
    app.logger.addHandler(logger)
    app.logger.setLevel(AppConfig.LOG_LEVEL)

    app.babel = Babel(app)

    return app
