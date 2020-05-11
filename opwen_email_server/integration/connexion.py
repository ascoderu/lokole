from opwen_email_server import config
from opwen_email_server.actions import CalculateNumberOfUsersMetric
from opwen_email_server.actions import CalculatePendingEmailsMetric
from opwen_email_server.actions import CreateClient
from opwen_email_server.actions import DeleteClient
from opwen_email_server.actions import DownloadClientEmails
from opwen_email_server.actions import GetClient
from opwen_email_server.actions import ListClients
from opwen_email_server.actions import Ping
from opwen_email_server.actions import ReceiveInboundEmail
from opwen_email_server.actions import UploadClientEmails
from opwen_email_server.integration.azure import get_auth
from opwen_email_server.integration.azure import get_client_storage
from opwen_email_server.integration.azure import get_email_storage
from opwen_email_server.integration.azure import get_mailbox_storage
from opwen_email_server.integration.azure import get_no_auth
from opwen_email_server.integration.azure import get_pending_storage
from opwen_email_server.integration.azure import get_raw_email_storage
from opwen_email_server.integration.azure import get_user_storage
from opwen_email_server.integration.celery import inbound_store
from opwen_email_server.integration.celery import process_service_email
from opwen_email_server.integration.celery import register_client
from opwen_email_server.integration.celery import written_store
from opwen_email_server.services.auth import BasicAuth
from opwen_email_server.services.auth import GithubAuth
from opwen_email_server.services.dns import DeleteMxRecords
from opwen_email_server.services.sendgrid import DeleteSendgridMailbox

email_receive = ReceiveInboundEmail(
    auth=get_auth(),
    raw_email_storage=get_raw_email_storage(),
    next_task=inbound_store.delay,
)

receive_service_email = ReceiveInboundEmail(
    auth=get_no_auth(),
    raw_email_storage=get_raw_email_storage(),
    next_task=process_service_email,
)

client_write = UploadClientEmails(
    auth=get_auth(),
    next_task=written_store.delay,
)

client_read = DownloadClientEmails(
    auth=get_auth(),
    client_storage=get_client_storage(),
    email_storage=get_email_storage(),
    pending_storage=get_pending_storage(),
)

client_create = CreateClient(
    auth=get_auth(),
    task=register_client.delay,
)

client_list = ListClients(auth=get_auth())

client_get = GetClient(
    auth=get_auth(),
    client_storage=get_client_storage(),
)

client_delete = DeleteClient(
    auth=get_auth(),
    delete_mailbox=DeleteSendgridMailbox(key=config.SENDGRID_KEY),
    delete_mx_records=DeleteMxRecords(
        account=config.DNS_ACCOUNT,
        secret=config.DNS_SECRET,
        provider=config.DNS_PROVIDER,
    ),
    mailbox_storage=get_mailbox_storage(),
    pending_storage=get_pending_storage(),
    user_storage=get_user_storage(),
)

metrics_users = CalculateNumberOfUsersMetric(
    auth=get_auth(),
    user_storage=get_user_storage(),
)

metrics_pending = CalculatePendingEmailsMetric(
    auth=get_auth(),
    pending_storage=get_pending_storage(),
)

basic_auth = BasicAuth(users={
    config.REGISTRATION_USERNAME: {'password': config.REGISTRATION_PASSWORD},
})

github_auth = GithubAuth(organization=config.REGISTRATION_GITHUB_ORGANIZATION)

healthcheck = Ping()
