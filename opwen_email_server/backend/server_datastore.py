from functools import lru_cache
from json import loads
from typing import Iterable

from opwen_email_server import azure_constants as constants
from opwen_email_server import config
from opwen_email_server.services.storage import AzureTextStorage
from opwen_email_server.utils.email_parser import get_domains
from opwen_email_server.utils.serialization import to_json


@lru_cache(maxsize=1)
def _get_email_storage():
    return AzureTextStorage(account=config.BLOBS_ACCOUNT,
                            key=config.BLOBS_KEY,
                            container=constants.CONTAINER_EMAILS,
                            provider=config.STORAGE_PROVIDER)


@lru_cache(maxsize=128)
def _get_pending_storage(domain: str) -> AzureTextStorage:
    return AzureTextStorage(account=config.TABLES_ACCOUNT,
                            key=config.TABLES_KEY,
                            container=domain,
                            provider=config.STORAGE_PROVIDER)


def fetch_email(email_id: str) -> dict:
    email_storage = _get_email_storage()

    serialized = email_storage.fetch_text(email_id)
    email = loads(serialized)
    return email


def fetch_pending_emails(domain: str) -> Iterable[dict]:
    pending_storage = _get_pending_storage(domain)

    for email_id in pending_storage:
        yield fetch_email(email_id)


def mark_emails_as_delivered(domain: str, email_ids: Iterable[str]):
    pending_storage = _get_pending_storage(domain)

    for email_id in email_ids:
        pending_storage.delete(email_id)


def store_inbound_email(email_id: str, email: dict):
    email_storage = _get_email_storage()
    email['_uid'] = email_id

    email_storage.store_text(email_id, to_json(email))

    for domain in get_domains(email):
        pending_storage = _get_pending_storage(domain)
        pending_storage.store_text(email_id, 'pending')


def store_outbound_email(email_id: str, email: dict):
    email_storage = _get_email_storage()
    email['_uid'] = email_id

    email_storage.store_text(email_id, to_json(email))
