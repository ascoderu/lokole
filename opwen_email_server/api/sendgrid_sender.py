from typing import Tuple

from opwen_email_server import config
from opwen_email_server.services.queue import AzureQueue

QUEUE = AzureQueue(account=config.STORAGE_ACCOUNT, key=config.STORAGE_KEY,
                   name='SengridOutboundEmails')


def send(email: dict) -> Tuple[str, int]:
    # TODO: implement
    return 'sent', 200
