from azure.storage.blob import BlockBlobService
from azure.storage.table import TableBatch
from azure.storage.table import TableService

from opwen_email_server.api import config
from opwen_email_server.utils.collections import to_iterable
from opwen_email_server.utils.email_parser import get_domains
from opwen_email_server.utils.serialization import to_json

CONTAINER_NAME = 'Emails'
TABLES = {
    'domain': get_domains,
    'to': lambda _: _.get('to') or [],
    'cc': lambda _: _.get('cc') or [],
    'bcc': lambda _: _.get('bcc') or [],
    'from': lambda _: to_iterable(_.get('from')),
}

BLOB_SERVICE = None  # type: BlockBlobService
TABLE_SERVICE = None  # type: TableService


def _index_email(email_id: str, email: dict):
    for table, values_getter in TABLES.items():
        batch = TableBatch()
        for value in values_getter(email):
            batch.insert_or_replace_entity({
                'PartitionKey': value,
                'RowKey': email_id,
            })
        TABLE_SERVICE.commit_batch(table, batch)


def _store_email(email_id: str, email: dict):
    serialized = to_json(email)
    BLOB_SERVICE.create_blob_from_text(CONTAINER_NAME, email_id, serialized)


def initialize(storage_account: str=config.STORAGE_ACCOUNT,
               storage_key: str=config.STORAGE_KEY,
               container_name: str=CONTAINER_NAME):
    global BLOB_SERVICE
    if BLOB_SERVICE is None:
        BLOB_SERVICE = BlockBlobService(storage_account, storage_key)
        BLOB_SERVICE.create_container(container_name)

    global TABLE_SERVICE
    if TABLE_SERVICE is None:
        TABLE_SERVICE = TableService(storage_account, storage_key)
        for table in TABLES:
            TABLE_SERVICE.create_table(table)


def store_email(email_id: str, email: dict):
    initialize()

    email['_uid'] = email_id

    _store_email(email_id, email)

    _index_email(email_id, email)
