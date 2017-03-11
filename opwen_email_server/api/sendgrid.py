from json import dumps
from os import getenv
from uuid import uuid4

from azure.storage.blob import BlockBlobService
from azure.storage.queue import QueueService


STORAGE_ACCOUNT = getenv('OPWEN_EMAIL_SERVER_AZURE_STORAGE_ACCOUNT_NAME')
STORAGE_KEY = getenv('OPWEN_EMAIL_SERVER_AZURE_STORAGE_ACCOUNT_KEY')
CONTAINER_NAME = 'SendgridInboundEmails'
QUEUE_NAME = 'SengridInboundEmails'

BLOB_SERVICE = None  # type: BlockBlobService
QUEUE_SERVICE = None  # type: QueueService


def initialize(storage_account=STORAGE_ACCOUNT, storage_key=STORAGE_KEY,
               container_name=CONTAINER_NAME, queue_name=QUEUE_NAME):
    """
    :type storage_account: str
    :type storage_key: str
    :type container_name: str
    :type queue_name: str

    """
    global BLOB_SERVICE
    if BLOB_SERVICE is None:
        BLOB_SERVICE = BlockBlobService(storage_account, storage_key)
        BLOB_SERVICE.create_container(container_name)

    global QUEUE_SERVICE
    if QUEUE_SERVICE is None:
        QUEUE_SERVICE = QueueService(storage_account, storage_key)
        QUEUE_SERVICE.create_queue(queue_name)


def create_message(email_id):
    """
    :type email_id: str
    :rtype: str

    """
    return dumps({
        '_version': '0.1',
        '_type': 'mime_email_received',
        '_received_by': 'sendgrid',
        'blob_name': email_id,
        'container_name': CONTAINER_NAME,
    }, separators=(',', ':'))


def receive(email):
    """
    :type email: str

    """
    initialize()

    email_id = str(uuid4())

    BLOB_SERVICE.create_blob_from_text(CONTAINER_NAME, email_id, email)

    QUEUE_SERVICE.put_message(QUEUE_NAME, create_message(email_id))

