from opwen_email_server.api import config
from opwen_email_server.services.index import AzureIndex
from opwen_email_server.services.storage import AzureStorage
from opwen_email_server.utils.collections import to_iterable
from opwen_email_server.utils.email_parser import get_domains
from opwen_email_server.utils.serialization import to_json

STORAGE = AzureStorage(account=config.STORAGE_ACCOUNT, key=config.STORAGE_KEY,
                       container='Emails')

INDEX = AzureIndex(account=config.STORAGE_ACCOUNT, key=config.STORAGE_KEY,
                   tables={
                       'domain': get_domains,
                       'to': lambda _: _.get('to') or [],
                       'cc': lambda _: _.get('cc') or [],
                       'bcc': lambda _: _.get('bcc') or [],
                       'from': lambda _: to_iterable(_.get('from')),
                       'domainXdelivered': lambda _: (
                           '{}_{}'.format(domain, _.get('_delivered') or False)
                           for domain in get_domains(_)),
                   })


def store_email(email_id: str, email: dict):
    email['_uid'] = email_id

    STORAGE.store_text(email_id, to_json(email))

    INDEX.insert(email_id, email)
