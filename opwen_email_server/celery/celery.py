from __future__ import absolute_import
from celery import Celery

celery = Celery(include = [ "opwen_email_server.api.store_written_client_emails",
                            "opwen_email_server.api.send_outbound_emails",
                            "opwen_email_server.api.store_inbound_emails"])

class Config:
    BROKER_URL = "amqp://"
    CELERY_RESULT_BACKEND = "amqp://"

celery.config_from_object(Config)


if __name__ == "__main__":
    celery.start()
