from opwen_email_server.actions import DownloadClientEmails
from opwen_email_server.actions import Ping
from opwen_email_server.actions import ReceiveInboundEmail
from opwen_email_server.actions import RegisterClient
from opwen_email_server.actions import UploadClientEmails
from opwen_email_server.integration.azure import get_auth
from opwen_email_server.integration.azure import get_client_storage
from opwen_email_server.integration.azure import get_email_storage
from opwen_email_server.integration.azure import get_pending_storage
from opwen_email_server.integration.azure import get_raw_email_storage
from opwen_email_server.integration.celery import inbound_store
from opwen_email_server.integration.celery import written_store
from opwen_email_server.integration.dns import SetupEmailDns

email_receive = ReceiveInboundEmail(
    auth=get_auth(),
    raw_email_storage=get_raw_email_storage(),
    next_task=inbound_store.delay)

client_write = UploadClientEmails(
    auth=get_auth(),
    next_task=written_store.delay)

client_read = DownloadClientEmails(
    auth=get_auth(),
    client_storage=get_client_storage(),
    email_storage=get_email_storage(),
    pending_factory=get_pending_storage)

client_register = RegisterClient(
    auth=get_auth(),
    client_storage=get_client_storage(),
    setup_email_dns=SetupEmailDns())

healthcheck = Ping()
