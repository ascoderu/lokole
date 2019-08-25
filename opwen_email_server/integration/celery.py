from celery import Celery

from opwen_email_server.actions import SendOutboundEmails
from opwen_email_server.actions import StoreInboundEmails
from opwen_email_server.actions import StoreWrittenClientEmails
from opwen_email_server.config import QUEUE_BROKER
from opwen_email_server.constants.queues import INBOUND_STORE_QUEUE
from opwen_email_server.constants.queues import SEND_QUEUE
from opwen_email_server.constants.queues import WRITTEN_STORE_QUEUE
from opwen_email_server.integration.azure import get_client_storage
from opwen_email_server.integration.azure import get_email_sender
from opwen_email_server.integration.azure import get_email_storage
from opwen_email_server.integration.azure import get_pending_storage
from opwen_email_server.integration.azure import get_raw_email_storage

celery = Celery(broker=QUEUE_BROKER)


@celery.task(ignore_result=True)
def inbound_store(resource_id: str) -> None:
    action = StoreInboundEmails(
        raw_email_storage=get_raw_email_storage(),
        email_storage=get_email_storage(),
        pending_factory=get_pending_storage)

    action(resource_id)


@celery.task(ignore_result=True)
def written_store(resource_id: str) -> None:
    action = StoreWrittenClientEmails(
        client_storage=get_client_storage(),
        email_storage=get_email_storage(),
        next_task=send.delay)

    action(resource_id)


@celery.task(ignore_result=True)
def send(resource_id: str) -> None:
    action = SendOutboundEmails(
        email_storage=get_email_storage(),
        send_email=get_email_sender())

    action(resource_id)


def _fqn(task):
    return f'{__name__}.{task.__name__}'


celery.conf.update(
    task_routes={
         _fqn(inbound_store): {'queue': INBOUND_STORE_QUEUE},
         _fqn(written_store): {'queue': WRITTEN_STORE_QUEUE},
         _fqn(send): {'queue': SEND_QUEUE}
    })


if __name__ == '__main__':
    celery.start()
