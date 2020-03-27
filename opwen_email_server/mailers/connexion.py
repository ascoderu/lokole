from opwen_email_server.action import ReceiveInboundEmail
from opwen_email_server.integration.azure import get_no_auth
from opwen_email_server.integration.azure import get_raw_email_storage
from opwen_email_server.integration.celery import process_service_email

receive_service_email = ReceiveInboundEmail(
    auth=get_no_auth(),
    raw_email_storage=get_raw_email_storage(),
    next_task=process_service_email,
)
