from typing import Optional

from celery import Celery

from opwen_email_client.webapp.actions import StartInternetConnection
from opwen_email_client.webapp.actions import SyncEmails
from opwen_email_client.webapp.actions import UpdateCode
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.ioc import Ioc

app = Celery(__name__, broker=AppConfig.CELERY_BROKER_URL)


@app.task(ignore_result=True)
def sync():
    sync_emails = SyncEmails(
        log=app.log,
        email_sync=Ioc.email_sync,
        email_store=Ioc.email_store)

    start_internet_connection = StartInternetConnection(
        modem_config_dir=AppConfig.MODEM_CONFIG_DIR,
        sim_config_dir=AppConfig.SIM_CONFIG_DIR,
        sim_type=AppConfig.SIM_TYPE)

    if AppConfig.SIM_TYPE != 'LocalOnly':
        with start_internet_connection():
            sync_emails()


@app.task(ignore_result=True)
def update(version: Optional[str]):
    update_code = UpdateCode(
        restart_paths=AppConfig.RESTART_PATHS,
        version=version,
        log=app.log)

    start_internet_connection = StartInternetConnection(
        modem_config_dir=AppConfig.MODEM_CONFIG_DIR,
        sim_config_dir=AppConfig.SIM_CONFIG_DIR,
        sim_type=AppConfig.SIM_TYPE)

    if AppConfig.SIM_TYPE != 'LocalOnly':
        with start_internet_connection():
            update_code()
