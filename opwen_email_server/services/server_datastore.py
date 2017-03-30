from json import loads

from opwen_email_server import config
from opwen_email_server.services.index import AzureIndex
from opwen_email_server.services.storage import AzureStorage
from opwen_email_server.utils.collections import to_iterable
from opwen_email_server.utils.email_parser import get_domains
from opwen_email_server.utils.serialization import to_json

STORAGE = AzureStorage(account=config.STORAGE_ACCOUNT, key=config.STORAGE_KEY,
                       container=config.CONTAINER_EMAILS)

INDEX = AzureIndex(
    account=config.STORAGE_ACCOUNT, key=config.STORAGE_KEY,
    tables={
        config.TABLE_DOMAIN: get_domains,
        config.TABLE_TO: lambda _: _.get('to') or [],
        config.TABLE_CC: lambda _: _.get('cc') or [],
        config.TABLE_BCC: lambda _: _.get('bcc') or [],
        config.TABLE_FROM: lambda _: to_iterable(_.get('from')),
        config.TABLE_DOMAIN_X_DELIVERED: lambda _: (
            '{}_{}'.format(domain, _.get('_delivered') or False)
            for domain in get_domains(_)),
        })


def fetch_email(email_id: str) -> dict:
    serialized = STORAGE.fetch_text(email_id)
    email = loads(serialized)
    return email


def store_email(email_id: str, email: dict):
    email['_uid'] = email_id

    STORAGE.store_text(email_id, to_json(email))

    INDEX.insert(email_id, email)
