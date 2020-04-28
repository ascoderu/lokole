from celery import Celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger

from opwen_email_client.webapp.actions import RestartApp
from opwen_email_client.webapp.actions import StartInternetConnection
from opwen_email_client.webapp.actions import SyncEmails
from opwen_email_client.webapp.actions import UpdateCode
from opwen_email_client.webapp.config import AppConfig

app = Celery(__name__, broker=AppConfig.CELERY_BROKER_URL)
app.conf.beat_schedule_filename = AppConfig.CELERY_BEAT_SCHEDULE_FILENAME
log = get_task_logger(__name__)


# noinspection PyUnusedLocal
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sync_schedule = AppConfig.SYNC_SCHEDULE.split(' ')
    if len(sync_schedule) == 5:
        sender.add_periodic_task(
            schedule=crontab(*sync_schedule),
            sig=sync.s('periodic_email_sync'),
        )


# noinspection PyUnusedLocal
@app.task(ignore_result=True)
def sync(*args, **kwargs):
    from opwen_email_client.webapp import app as webapp

    sync_emails = SyncEmails(
        log=log,
        email_sync=webapp.ioc.email_sync,
        email_store=webapp.ioc.email_store,
        user_store=webapp.ioc.user_store,
    )

    start_internet_connection = StartInternetConnection(
        state_dir=AppConfig.STATE_BASEDIR,
        modem_config_dir=AppConfig.MODEM_CONFIG_DIR,
        sim_config_dir=AppConfig.SIM_CONFIG_DIR,
        sim_type=AppConfig.SIM_TYPE,
    )

    if AppConfig.SIM_TYPE != 'LocalOnly':
        with start_internet_connection():
            sync_emails()


# noinspection PyUnusedLocal
@app.task(ignore_result=True)
def update(*args, **kwargs):
    update_code = UpdateCode(
        version=kwargs.get('version') or '',
        log=log,
    )

    restart_app = RestartApp(restart_paths=AppConfig.RESTART_PATHS)

    start_internet_connection = StartInternetConnection(
        state_dir=AppConfig.STATE_BASEDIR,
        modem_config_dir=AppConfig.MODEM_CONFIG_DIR,
        sim_config_dir=AppConfig.SIM_CONFIG_DIR,
        sim_type=AppConfig.SIM_TYPE,
    )

    if AppConfig.SIM_TYPE != 'LocalOnly':
        with start_internet_connection():
            update_code()

        restart_app()
