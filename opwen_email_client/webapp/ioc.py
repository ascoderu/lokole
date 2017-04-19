from logging import Formatter
from logging import StreamHandler

from azure.storage.blob import BlockBlobService
from flask import Flask
from flask_babel import Babel

from opwen_email_client.domain.email.attachment import Base64AttachmentEncoder
from opwen_email_client.domain.email.sql_store import SqliteEmailStore
from opwen_email_client.domain.email.sync import AzureSync
from opwen_email_client.util.serialization import JsonSerializer
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.session import AttachmentsStore


class Ioc(object):
    serializer = JsonSerializer()

    azure_client = BlockBlobService(
        account_name=AppConfig.STORAGE_ACCOUNT_NAME,
        account_key=AppConfig.STORAGE_ACCOUNT_KEY)

    email_store = SqliteEmailStore(
        database_path=AppConfig.LOCAL_EMAIL_STORE,
        serializer=serializer)

    email_sync = AzureSync(
        azure_client=azure_client,
        container=AppConfig.STORAGE_CONTAINER,
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

    handler = StreamHandler()
    handler.setFormatter(Formatter(AppConfig.LOG_FORMAT))
    app.logger.addHandler(handler)
    app.logger.setLevel(AppConfig.LOG_LEVEL)

    app.babel = Babel(app)

    return app
