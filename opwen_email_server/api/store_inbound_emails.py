from opwen_email_server import events
from opwen_email_server.backend import server_datastore
from opwen_email_server.utils.email_parser import get_domain
from opwen_email_server.utils.email_parser import format_attachments
from opwen_email_server.utils.email_parser import format_inline_images
from opwen_email_server.utils.email_parser import parse_mime_email
from opwen_email_server.utils.log import LogMixin

from opwen_email_server.celery.celery import celery

logger = LogMixin()

@celery.task
def store(resource_id: str):
    mime_email = email_receive.STORAGE.fetch_text(resource_id)

    email = parse_mime_email(mime_email)
    email = format_attachments(email)
    email = format_inline_images(email)
    server_datastore.store_inbound_email(resource_id, email)

    email_receive.STORAGE.delete(resource_id)

    logger.log_event(events.EMAIL_STORED_FOR_CLIENT, {'domain': get_domain(email.get('from', ''))})  # noqa: E501
    return 'OK', 200
