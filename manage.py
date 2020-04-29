#!/usr/bin/env python3
from glob import glob
from os import getenv
from os import remove
from os.path import join
from pathlib import Path
from threading import Event

from flask_migrate import MigrateCommand
from flask_script import Manager
from flask_security.utils import hash_password
from watchdog.events import FileSystemEvent
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from opwen_email_client.webapp import app
from opwen_email_client.webapp.actions import RestartAppComponent
from opwen_email_client.webapp.config import AppConfig

manager = Manager(app)
manager.add_command('db', MigrateCommand)


@manager.command
def devserver():
    templates_directory = join(app.root_path, app.template_folder)
    templates_glob = join(templates_directory, '**', '*.html')
    reload_server_if_changed = glob(templates_glob, recursive=True)

    port = int(getenv('WEBAPP_PORT', '5000'))
    host = getenv('HOST', '127.0.0.1')

    app.run(debug=True, extra_files=reload_server_if_changed, host=host, port=port)  # nosec


@manager.command
def resetdb():
    remove(AppConfig.LOCAL_EMAIL_STORE)
    remove(AppConfig.SQLITE_PATH)


@manager.option('-d', '--directory', required=True)
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


@manager.option('-n', '--name', required=True)
@manager.option('-p', '--password', required=True)
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


if __name__ == '__main__':
    manager.run()
