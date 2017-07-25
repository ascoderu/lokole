from json import loads
from typing import Iterable

from opwen_email_server import config
from opwen_email_server.services.index import AzureIndex
from opwen_email_server.services.storage import AzureTextStorage
from opwen_email_server.utils.collections import to_iterable
from opwen_email_server.utils.email_parser import get_domains
from opwen_email_server.utils.serialization import to_json

STORAGE = AzureTextStorage(account=config.BLOBS_ACCOUNT,
                           key=config.BLOBS_KEY,
                           container=config.CONTAINER_EMAILS)

INDEX = AzureIndex(
    account=config.TABLES_ACCOUNT, key=config.TABLES_KEY,
    tables={
        config.TABLE_DOMAIN: get_domains,
        config.TABLE_TO: lambda _: _.get('to') or [],
        config.TABLE_CC: lambda _: _.get('cc') or [],
        config.TABLE_BCC: lambda _: _.get('bcc') or [],
        config.TABLE_FROM: lambda _: to_iterable(_.get('from')),
        config.TABLE_DOMAIN_X_DELIVERED: lambda _: (
            '{domain}_{delivered}'.format(
                domain=domain,
                delivered=_.get('_delivered') or False)
            for domain in get_domains(_)),
        })


def fetch_email(email_id: str) -> dict:
    serialized = STORAGE.fetch_text(email_id)
    email = loads(serialized)
    return email


def fetch_pending_emails(domain: str) -> Iterable[dict]:
    partition = '{domain}_{delivered}'.format(domain=domain, delivered=False)
    email_ids = INDEX.query(config.TABLE_DOMAIN_X_DELIVERED, partition)
    for email_id in email_ids:
        yield fetch_email(email_id)


def mark_emails_as_delivered(domain: str, email_ids: Iterable[str]):
    partition = '{domain}_{delivered}'.format(domain=domain, delivered=False)
    INDEX.delete(config.TABLE_DOMAIN_X_DELIVERED, partition, email_ids)


def store_email(email_id: str, email: dict):
    email['_uid'] = email_id

    STORAGE.store_text(email_id, to_json(email))

    INDEX.insert(email_id, email)
