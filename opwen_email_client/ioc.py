from flask import Flask
from flask_babel import Babel
from opwen_domain.config import OpwenConfig
from opwen_domain.email.base64 import Base64AttachmentEncoder
from opwen_domain.email.memory import PersistentInMemoryEmailStore
from opwen_domain.sync.azure import AzureSync
from opwen_infrastructure.serialization.json import JsonSerializer

from opwen_email_client.config import FlaskConfig


class Ioc(object):
    email_store = PersistentInMemoryEmailStore(
        store_location=FlaskConfig.LOCAL_EMAIL_STORE)

    email_sync = AzureSync(
        account_name=OpwenConfig.STORAGE_ACCOUNT_NAME,
        account_key=OpwenConfig.STORAGE_ACCOUNT_KEY,
        container=OpwenConfig.STORAGE_CONTAINER,
        download_location=OpwenConfig.STORAGE_DOWNLOAD_PATH,
        upload_location=OpwenConfig.STORAGE_UPLOAD_PATH,
        serializer=JsonSerializer())

    attachment_encoder = Base64AttachmentEncoder()


def create_app():
    """
    :rtype: flask.Flask

    """
    app = Flask(__name__)
    app.config.from_object(FlaskConfig)
    app.ioc = Ioc()

    Babel(app)

    return app
