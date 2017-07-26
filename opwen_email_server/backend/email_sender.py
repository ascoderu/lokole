from typing import Tuple

from opwen_email_server import azure_constants as constants
from opwen_email_server import config
from opwen_email_server.services.queue import AzureQueue
from opwen_email_server.services.sendgrid import SendgridEmailSender

QUEUE = AzureQueue(account=config.QUEUES_ACCOUNT, key=config.QUEUES_KEY,
                   name=constants.QUEUE_EMAIL_SEND)

EMAIL = SendgridEmailSender(key=config.EMAIL_SENDER_KEY)


def send(email: dict) -> Tuple[str, int]:
    success = EMAIL.send_email(email)

    if not success:
        return 'error', 500

    return 'sent', 200
