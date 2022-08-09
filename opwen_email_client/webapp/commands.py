from os import remove
from pathlib import Path
from threading import Event

import click
from flask import Blueprint
from flask import current_app as app
from flask_security.utils import hash_password
from watchdog.events import FileSystemEvent
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from opwen_email_client.webapp.actions import RestartAppComponent
from opwen_email_client.webapp.config import AppConfig

managesbp = Blueprint('manage', __name__)


@managesbp.cli.command('resetdb')
def resetdb():
    remove(AppConfig.LOCAL_EMAIL_STORE)
    remove(AppConfig.SQLITE_PATH)


@managesbp.cli.command("restarter")
@click.option('-d', '--directory', required=True)
def restarter(directory):

    class Restarter(FileSystemEventHandler):

        def on_created(self, event: FileSystemEvent):
            restart = RestartAppComponent(restart_path=event.src_path)
            restart()

    Path(directory).mkdir(exist_ok=True, parents=True)
    observer = Observer()
    observer.schedule(Restarter(), directory)
    observer.start()
    try:
        Event().wait()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


@managesbp.cli.command('createadmin')
@click.option('--name', required=True)
@click.option('--password', required=True)
def createadmin(name, password):
    user_datastore = app.ioc.user_store
    email = '{}@{}'.format(name, AppConfig.CLIENT_EMAIL_HOST)
    password = hash_password(password)

    user = user_datastore.r.find_user(email=email)
    if user is None:
        user_datastore.w.create_user(email=email, password=password, is_admin=True)
    else:
        user.is_admin = True
        user.password = password
        user_datastore.w.put(user)

    user_datastore.w.commit()
