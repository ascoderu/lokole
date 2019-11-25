from celery import Celery

from opwen_email_server.actions import IndexReceivedEmailForMailbox
from opwen_email_server.actions import IndexSentEmailForMailbox
from opwen_email_server.actions import RegisterClient
from opwen_email_server.actions import SendOutboundEmails
from opwen_email_server.actions import StoreInboundEmails
from opwen_email_server.actions import StoreWrittenClientEmails
from opwen_email_server.config import QUEUE_BROKER
from opwen_email_server.constants.queues import INBOUND_STORE_QUEUE
from opwen_email_server.constants.queues import MAILBOX_RECEIVED_QUEUE
from opwen_email_server.constants.queues import MAILBOX_SENT_QUEUE
from opwen_email_server.constants.queues import REGISTER_CLIENT_QUEUE
from opwen_email_server.constants.queues import SEND_QUEUE
from opwen_email_server.constants.queues import WRITTEN_STORE_QUEUE
from opwen_email_server.integration.azure import get_auth
from opwen_email_server.integration.azure import get_client_storage
from opwen_email_server.integration.azure import get_email_sender
from opwen_email_server.integration.azure import get_email_storage
from opwen_email_server.integration.azure import get_mailbox_setup
from opwen_email_server.integration.azure import get_mailbox_storage
from opwen_email_server.integration.azure import get_mx_setup
from opwen_email_server.integration.azure import get_pending_storage
from opwen_email_server.integration.azure import get_raw_email_storage

celery = Celery(broker=QUEUE_BROKER)


@celery.task(ignore_result=True)
def register_client(domain: str, owner: str) -> None:
    action = RegisterClient(
        auth=get_auth(),
        client_storage=get_client_storage(),
        setup_mailbox=get_mailbox_setup(),
        setup_mx_records=get_mx_setup(),
    )

    action(domain, owner)


@celery.task(ignore_result=True)
def index_received_email_for_mailbox(resource_id: str) -> None:
    action = IndexReceivedEmailForMailbox(
        email_storage=get_email_storage(),
        mailbox_storage=get_mailbox_storage(),
    )

    action(resource_id)


@celery.task(ignore_result=True)
def index_sent_email_for_mailbox(resource_id: str) -> None:
    action = IndexSentEmailForMailbox(
        email_storage=get_email_storage(),
        mailbox_storage=get_mailbox_storage(),
    )

    action(resource_id)


@celery.task(ignore_result=True)
def inbound_store(resource_id: str) -> None:
    action = StoreInboundEmails(
        raw_email_storage=get_raw_email_storage(),
        email_storage=get_email_storage(),
        pending_factory=get_pending_storage,
        next_task=index_received_email_for_mailbox.delay,
    )

    action(resource_id)


def _send_and_index(resource_id: str) -> None:
    send.delay(resource_id)
    index_sent_email_for_mailbox.delay(resource_id)


@celery.task(ignore_result=True)
def written_store(resource_id: str) -> None:
    action = StoreWrittenClientEmails(
        client_storage=get_client_storage(),
        email_storage=get_email_storage(),
        next_task=_send_and_index,
    )

    action(resource_id)


@celery.task(ignore_result=True)
def send(resource_id: str) -> None:
    action = SendOutboundEmails(
        email_storage=get_email_storage(),
        send_email=get_email_sender(),
    )

    action(resource_id)


def _fqn(task):
    return f'{__name__}.{task.__name__}'


celery.conf.update(
    task_routes={
        _fqn(register_client): {'queue': REGISTER_CLIENT_QUEUE},
        _fqn(index_received_email_for_mailbox): {'queue': MAILBOX_RECEIVED_QUEUE},
        _fqn(index_sent_email_for_mailbox): {'queue': MAILBOX_SENT_QUEUE},
        _fqn(inbound_store): {'queue': INBOUND_STORE_QUEUE},
        _fqn(written_store): {'queue': WRITTEN_STORE_QUEUE},
        _fqn(send): {'queue': SEND_QUEUE}
    })

if __name__ == '__main__':
    celery.start()
