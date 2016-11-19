from logging import Formatter
from logging import StreamHandler

from flask import Flask
from flask_babel import Babel
from opwen_domain.email.base64 import Base64AttachmentEncoder
from opwen_domain.email.tinydb import TinyDbEmailStore
from opwen_domain.sync.azure import AzureAuth
from opwen_domain.sync.azure import AzureSync
from opwen_infrastructure.serialization.json import JsonSerializer

from opwen_email_client.config import AppConfig


class Ioc(object):
    email_store = TinyDbEmailStore(
        store_location=AppConfig.LOCAL_EMAIL_STORE)

    email_sync = AzureSync(
        auth=AzureAuth(
            account=AppConfig.STORAGE_ACCOUNT_NAME,
            key=AppConfig.STORAGE_ACCOUNT_KEY,
            container=AppConfig.STORAGE_CONTAINER),
        download_locations=[AppConfig.STORAGE_DOWNLOAD_PATH],
        upload_locations=[AppConfig.STORAGE_UPLOAD_PATH],
        serializer=JsonSerializer())

    attachment_encoder = Base64AttachmentEncoder()


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

    Babel(app)

    return app
