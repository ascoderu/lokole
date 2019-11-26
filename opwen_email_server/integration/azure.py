from functools import lru_cache

from opwen_email_server import config
from opwen_email_server.constants import azure as constants
from opwen_email_server.constants.cache import PENDING_STORAGE_CACHE_SIZE
from opwen_email_server.services.auth import AzureAuth
from opwen_email_server.services.storage import AzureFileStorage
from opwen_email_server.services.storage import AzureObjectsStorage
from opwen_email_server.services.storage import AzureObjectStorage
from opwen_email_server.services.storage import AzureTextStorage
from opwen_email_server.utils.collections import singleton


@singleton
def get_auth() -> AzureAuth:
    return AzureAuth(storage=AzureTextStorage(
        account=config.TABLES_ACCOUNT,
        key=config.TABLES_KEY,
        host=config.TABLES_HOST,
        secure=config.TABLES_SECURE,
        container=constants.TABLE_AUTH,
        provider=config.STORAGE_PROVIDER,
    ))


@singleton
def get_client_storage() -> AzureObjectsStorage:
    return AzureObjectsStorage(file_storage=AzureFileStorage(
        account=config.CLIENT_STORAGE_ACCOUNT,
        key=config.CLIENT_STORAGE_KEY,
        host=config.CLIENT_STORAGE_HOST,
        secure=config.CLIENT_STORAGE_SECURE,
        container=constants.CONTAINER_CLIENT_PACKAGES,
        provider=config.STORAGE_PROVIDER,
    ))


@singleton
def get_raw_email_storage() -> AzureTextStorage:
    return AzureTextStorage(
        account=config.BLOBS_ACCOUNT,
        key=config.BLOBS_KEY,
        host=config.BLOBS_HOST,
        secure=config.BLOBS_SECURE,
        container=constants.CONTAINER_SENDGRID_MIME,
        provider=config.STORAGE_PROVIDER,
    )


@singleton
def get_email_storage() -> AzureObjectStorage:
    return AzureObjectStorage(
        account=config.BLOBS_ACCOUNT,
        key=config.BLOBS_KEY,
        host=config.BLOBS_HOST,
        secure=config.BLOBS_SECURE,
        container=constants.CONTAINER_EMAILS,
        provider=config.STORAGE_PROVIDER,
    )


@singleton
def get_mailbox_storage() -> AzureObjectStorage:
    return AzureObjectStorage(
        account=config.BLOBS_ACCOUNT,
        key=config.BLOBS_KEY,
        host=config.BLOBS_HOST,
        secure=config.BLOBS_SECURE,
        container=constants.CONTAINER_MAILBOX,
        provider=config.STORAGE_PROVIDER,
    )


@lru_cache(maxsize=PENDING_STORAGE_CACHE_SIZE)
def get_pending_storage(domain: str) -> AzureTextStorage:
    container = domain.replace('.', '-')
    return AzureTextStorage(
        account=config.TABLES_ACCOUNT,
        key=config.TABLES_KEY,
        host=config.TABLES_HOST,
        secure=config.TABLES_SECURE,
        container=container,
        provider=config.STORAGE_PROVIDER,
    )
