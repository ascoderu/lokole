from celery import Celery

from opwen_email_server import config
from opwen_email_server.api import send_outbound_emails
from opwen_email_server.api import store_inbound_emails
from opwen_email_server.api import store_written_client_emails

celery = Celery(broker=config.QUEUE_BROKER)


@celery.task(ignore_result=True)
def inbound_store(resource_id: str) -> None:
    store_inbound_emails.store(resource_id)


@celery.task(ignore_result=True)
def written_store(resource_id: str) -> None:
    store_written_client_emails.store(resource_id)


@celery.task(ignore_result=True)
def send(resource_id: str) -> None:
    send_outbound_emails.send(resource_id)


if __name__ == "__main__":
    celery.start()
