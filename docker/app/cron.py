from logging import getLogger
from os import getenv
from signal import SIGINT
from signal import SIGTERM
from signal import signal
from time import sleep

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.events import EVENT_JOB_EXECUTED
import requests

sched = BlockingScheduler()
log = getLogger('lokole.sync')


def job():
    sync_url = 'http://localhost/sync?secret={secret}'.format(
        secret=getenv('OPWEN_ADMIN_SECRET', ''))

    response = requests.get(sync_url)
    response.raise_for_status()


def listener(event):
    if event.exception:
        log.error('Sync job failed %s', event.exception)
    else:
        log.debug('Sync job ran')


def shutdown(signum, frame):
    sched.shutdown()


if __name__ == '__main__':
    sync_schedule = getenv('OPWEN_SYNC_SCHEDULE')
    if not sync_schedule:
        log.warning('No OPWEN_SYNC_SCHEDULE set, no cron running')
        sleep(2)
        exit(99)
    else:
        sched.add_job(job, CronTrigger.from_crontab(sync_schedule))
        sched.add_listener(listener, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)
        signal(SIGINT, shutdown)
        signal(SIGTERM, shutdown)
        sched.start()
        exit(0)
