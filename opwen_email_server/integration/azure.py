from opwen_email_server import config
from opwen_email_server.services.auth import Auth
from opwen_email_server.services.auth import AzureAuth
from opwen_email_server.services.auth import NoAuth
from opwen_email_server.services.storage import AzureFileStorage
from opwen_email_server.services.storage import AzureObjectsStorage
from opwen_email_server.services.storage import AzureObjectStorage
from opwen_email_server.services.storage import AzureTextStorage
from opwen_email_server.utils.collections import singleton
from opwen_email_server.utils.unique import NewGuid


def get_no_auth() -> NoAuth:
    return NoAuth()


@singleton
def get_guid_source() -> NewGuid:
    return NewGuid(config.RANDOM_SEED)


@singleton
def get_auth() -> Auth:
    return AzureAuth(
        storage=AzureObjectStorage(
            account=config.TABLES_ACCOUNT,
            key=config.TABLES_KEY,
            host=config.TABLES_HOST,
            secure=config.TABLES_SECURE,
            container=config.CONTAINER_AUTH,
            provider=config.STORAGE_PROVIDER,
        ),
        sudo_scope=config.REGISTRATION_SUDO_TEAM,
    )


@singleton
def get_client_storage() -> AzureObjectsStorage:
    return AzureObjectsStorage(
        file_storage=AzureFileStorage(
            account=config.CLIENT_STORAGE_ACCOUNT,
            key=config.CLIENT_STORAGE_KEY,
            host=config.CLIENT_STORAGE_HOST,
            secure=config.CLIENT_STORAGE_SECURE,
            container=config.CONTAINER_CLIENT_PACKAGES,
            provider=config.STORAGE_PROVIDER,
        ),
        resource_id_source=get_guid_source(),
    )


@singleton
def get_raw_email_storage() -> AzureTextStorage:
    return AzureTextStorage(
        account=config.BLOBS_ACCOUNT,
        key=config.BLOBS_KEY,
        host=config.BLOBS_HOST,
        secure=config.BLOBS_SECURE,
        container=config.CONTAINER_SENDGRID_MIME,
        provider=config.STORAGE_PROVIDER,
    )


@singleton
def get_email_storage() -> AzureObjectStorage:
    return AzureObjectStorage(
        account=config.BLOBS_ACCOUNT,
        key=config.BLOBS_KEY,
        host=config.BLOBS_HOST,
        secure=config.BLOBS_SECURE,
        container=config.CONTAINER_EMAILS,
        provider=config.STORAGE_PROVIDER,
    )


@singleton
def get_user_storage() -> AzureObjectStorage:
    return AzureObjectStorage(
        account=config.TABLES_ACCOUNT,
        key=config.TABLES_KEY,
        host=config.TABLES_HOST,
        secure=config.TABLES_SECURE,
        container=config.CONTAINER_USERS,
        provider=config.STORAGE_PROVIDER,
        case_sensitive=False,
    )


@singleton
def get_mailbox_storage() -> AzureTextStorage:
    return AzureTextStorage(
        account=config.BLOBS_ACCOUNT,
        key=config.BLOBS_KEY,
        host=config.BLOBS_HOST,
        secure=config.BLOBS_SECURE,
        container=config.CONTAINER_MAILBOX,
        provider=config.STORAGE_PROVIDER,
        case_sensitive=False,
    )


@singleton
def get_pending_storage() -> AzureTextStorage:
    return AzureTextStorage(
        account=config.TABLES_ACCOUNT,
        key=config.TABLES_KEY,
        host=config.TABLES_HOST,
        secure=config.TABLES_SECURE,
        container=config.CONTAINER_PENDING,
        provider=config.STORAGE_PROVIDER,
    )
