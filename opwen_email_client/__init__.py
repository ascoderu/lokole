# pylint: disable=wrong-import-position
from opwen_email_client.ioc import create_app

app = create_app()

from opwen_email_client import login
from opwen_email_client import views

from opwen_email_client.crons import setup_email_sync_cron

setup_email_sync_cron()
