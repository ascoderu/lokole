from opwen_email_client import app
from opwen_email_client.actions import SyncEmails
from opwen_email_client.config import AppConfig
from opwen_infrastructure.cron import setup_cronjob
from opwen_infrastructure.logging import log_execution


@log_execution(app.logger)
def setup_email_sync_cron():
    sync_hour = str(AppConfig.EMAIL_SYNC_HOUR_UTC)
    setup_cronjob(hour_utc=sync_hour,
                  method=emails_sync,
                  logger=app.logger,
                  description='Sync Opwen emails at {} UTC'.format(sync_hour))


@log_execution(app.logger)
def emails_sync():
    sync_emails = SyncEmails(
        email_sync=app.ioc.email_sync,
        email_store=app.ioc.email_store,
        internet_interface=AppConfig.INTERNET_INTERFACE_NAME)

    sync_emails()
