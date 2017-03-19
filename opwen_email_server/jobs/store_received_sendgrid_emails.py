from time import sleep
from typing import Tuple

from opwen_email_server.api import sendgrid
from opwen_email_server.services import datastore
from opwen_email_server.utils.email_parser import parse_mime_email


def _load_email_content(message: dict) -> Tuple[str, str]:
    email_id = message['resource_id']
    mime_email = sendgrid.STORAGE.fetch_text(email_id)
    return email_id, mime_email


def _process_message(message: dict):
    email_id, mime_email = _load_email_content(message)
    email = parse_mime_email(mime_email)
    email['_delivered'] = False
    datastore.store_email(email_id, email)


def run_once(batch_size: int=1, lock_seconds: int=60):
    for message in sendgrid.QUEUE.dequeue(batch_size, lock_seconds):
        _process_message(message)


def run_forever(poll_seconds: int=10, batch_size: int=1, lock_seconds: int=60):
    while True:
        run_once(batch_size, lock_seconds)
        sleep(poll_seconds)


if __name__ == '__main__':
    run_forever()
