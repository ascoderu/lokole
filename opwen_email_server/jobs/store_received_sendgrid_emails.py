from time import sleep

from opwen_email_server.api import datastore
from opwen_email_server.api import sendgrid
from opwen_email_server.utils.email_parser import parse_mime_email


def _load_email_content(message):
    """
    :type message: str
    :rtype: (str, str)

    """
    email_id = sendgrid.parse_message(message)
    mime_email = sendgrid.BLOB_SERVICE.get_blob_to_text(
        sendgrid.CONTAINER_NAME, email_id)
    return email_id, mime_email


def _process_message(message):
    """
    :type message: str

    """
    email_id, mime_email = _load_email_content(message)
    email = parse_mime_email(mime_email)
    datastore.store_email(email_id, email)


def run_once(batch_size=1, lock_seconds=60):
    """
    :type batch_size: int
    :type lock_seconds: int

    """
    messages = sendgrid.QUEUE_SERVICE.get_messages(
        sendgrid.QUEUE_NAME, batch_size, lock_seconds)

    for message in messages:
        _process_message(message.content)

        sendgrid.QUEUE_SERVICE.delete_message(
            sendgrid.QUEUE_NAME, message.id, message.pop_receipt)


def run_forever(poll_seconds=10, batch_size=1, lock_seconds=60):
    """
    :type poll_seconds: int
    :type batch_size: int
    :type lock_seconds: int

    """
    sendgrid.initialize()
    datastore.initialize()

    while True:
        run_once(batch_size, lock_seconds)
        sleep(poll_seconds)


if __name__ == '__main__':
    run_forever()
