from opwen_email_server import config
from opwen_email_server.actions import CalculatePendingEmailsMetric
from opwen_email_server.actions import DownloadClientEmails
from opwen_email_server.actions import Ping
from opwen_email_server.actions import ReceiveInboundEmail
from opwen_email_server.actions import RegisterClient
from opwen_email_server.actions import UploadClientEmails
from opwen_email_server.integration.azure import get_auth
from opwen_email_server.integration.azure import get_client_storage
from opwen_email_server.integration.azure import get_email_storage
from opwen_email_server.integration.azure import get_mailbox_setup
from opwen_email_server.integration.azure import get_mx_setup
from opwen_email_server.integration.azure import get_pending_storage
from opwen_email_server.integration.azure import get_raw_email_storage
from opwen_email_server.integration.celery import inbound_store
from opwen_email_server.integration.celery import written_store
from opwen_email_server.services.auth import BasicAuth

email_receive = ReceiveInboundEmail(
    auth=get_auth(),
    raw_email_storage=get_raw_email_storage(),
    next_task=inbound_store.delay,
)

client_write = UploadClientEmails(
    auth=get_auth(),
    next_task=written_store.delay,
)

client_read = DownloadClientEmails(
    auth=get_auth(),
    client_storage=get_client_storage(),
    email_storage=get_email_storage(),
    pending_factory=get_pending_storage,
)

client_register = RegisterClient(
    auth=get_auth(),
    client_storage=get_client_storage(),
    setup_mailbox=get_mailbox_setup(),
    setup_mx_records=get_mx_setup(),
)

metrics_pending = CalculatePendingEmailsMetric(
    auth=get_auth(),
    pending_factory=get_pending_storage,
)

basic_auth = BasicAuth(users={config.REGISTRATION_USERNAME: {
    'password': config.REGISTRATION_PASSWORD,
}})

healthcheck = Ping()
