from celery import Celery

from opwen_email_server import config
from opwen_email_server.actions import IndexReceivedEmailForMailbox
from opwen_email_server.actions import IndexSentEmailForMailbox
from opwen_email_server.actions import ProcessServiceEmail
from opwen_email_server.actions import RegisterClient
from opwen_email_server.actions import SendOutboundEmails
from opwen_email_server.actions import StoreInboundEmails
from opwen_email_server.actions import StoreWrittenClientEmails
from opwen_email_server.integration.azure import get_auth
from opwen_email_server.integration.azure import get_client_storage
from opwen_email_server.integration.azure import get_email_storage
from opwen_email_server.integration.azure import get_guid_source
from opwen_email_server.integration.azure import get_mailbox_storage
from opwen_email_server.integration.azure import get_pending_storage
from opwen_email_server.integration.azure import get_raw_email_storage
from opwen_email_server.integration.azure import get_user_storage
from opwen_email_server.mailers import REGISTRY
from opwen_email_server.services.dns import SetupMxRecords
from opwen_email_server.services.sendgrid import SendSendgridEmail
from opwen_email_server.services.sendgrid import SetupSendgridMailbox

celery = Celery(broker=config.QUEUE_BROKER)


@celery.task(ignore_result=True)
def register_client(domain: str, owner: str) -> None:
    action = RegisterClient(
        auth=get_auth(),
        client_storage=get_client_storage(),
        setup_mailbox=SetupSendgridMailbox(
            key=config.SENDGRID_KEY,
            max_retries=config.SENDGRID_MAX_RETRIES,
            retry_interval_seconds=config.SENDGRID_RETRY_INTERVAL_SECONDS,
        ),
        setup_mx_records=SetupMxRecords(
            account=config.DNS_ACCOUNT,
            secret=config.DNS_SECRET,
            provider=config.DNS_PROVIDER,
        ),
        client_id_source=get_guid_source(),
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
        pending_storage=get_pending_storage(),
        next_task=index_received_email_for_mailbox.delay,
    )

    action(resource_id)


def send_and_index_email(resource_id: str) -> None:
    send.delay(resource_id)
    index_sent_email_for_mailbox.delay(resource_id)
    index_received_email_for_mailbox.delay(resource_id)


@celery.task(ignore_result=True)
def written_store(resource_id: str) -> None:
    action = StoreWrittenClientEmails(
        client_storage=get_client_storage(),
        email_storage=get_email_storage(),
        user_storage=get_user_storage(),
        next_task=send_and_index_email,
    )

    action(resource_id)


@celery.task(ignore_result=True)
def send(resource_id: str) -> None:
    action = SendOutboundEmails(
        email_storage=get_email_storage(),
        send_email=SendSendgridEmail(key=config.SENDGRID_KEY),
    )

    action(resource_id)


@celery.task(ignore_result=True)
def process_service_email(resource_id: str) -> None:
    action = ProcessServiceEmail(
        raw_email_storage=get_raw_email_storage(),
        email_storage=get_email_storage(),
        registry=REGISTRY,
        next_task=send_and_index_email,
    )

    action(resource_id)


def _fqn(task):
    return f'{__name__}.{task.__name__}'


task_routes = {
    _fqn(register_client): {'queue': config.REGISTER_CLIENT_QUEUE},
    _fqn(index_received_email_for_mailbox): {'queue': config.MAILBOX_RECEIVED_QUEUE},
    _fqn(index_sent_email_for_mailbox): {'queue': config.MAILBOX_SENT_QUEUE},
    _fqn(process_service_email): {'queue': config.PROCESS_SERVICE_QUEUE},
    _fqn(inbound_store): {'queue': config.INBOUND_STORE_QUEUE},
    _fqn(written_store): {'queue': config.WRITTEN_STORE_QUEUE},
    _fqn(send): {'queue': config.SEND_QUEUE}
}

celery.conf.update(task_routes=task_routes)

if __name__ == '__main__':
    celery.start()
