from json import loads
from typing import Iterable

from opwen_email_server.backend.services import get_email_storage
from opwen_email_server.backend.services import get_pending_storage
from opwen_email_server.utils.email_parser import get_domains
from opwen_email_server.utils.serialization import to_json


def fetch_email(email_id: str) -> dict:
    email_storage = get_email_storage()
    serialized = email_storage.fetch_text(email_id)
    email = loads(serialized)
    return email


def fetch_pending_emails(domain: str) -> Iterable[dict]:
    pending_storage = get_pending_storage(domain)

    for email_id in pending_storage:
        yield fetch_email(email_id)


def mark_emails_as_delivered(domain: str, email_ids: Iterable[str]):
    pending_storage = get_pending_storage(domain)

    for email_id in email_ids:
        pending_storage.delete(email_id)


def store_inbound_email(email_id: str, email: dict):
    email_storage = get_email_storage()
    email['_uid'] = email_id

    email_storage.store_text(email_id, to_json(email))

    for domain in get_domains(email):
        pending_storage = get_pending_storage(domain)
        pending_storage.store_text(email_id, 'pending')


def store_outbound_email(email_id: str, email: dict):
    email_storage = get_email_storage()
    email['_uid'] = email_id

    email_storage.store_text(email_id, to_json(email))
