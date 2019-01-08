#!/usr/bin/env python3
from glob import glob
from os import remove
from os.path import join
from typing import List

from flask_migrate import MigrateCommand
from flask_script import Manager

from opwen_email_client.webapp import app
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.login import user_datastore

manager = Manager(app)
manager.add_command('db', MigrateCommand)


def _templates_paths_for(templates_matcher: str) -> List[str]:
    templates_directory = join(app.root_path, app.template_folder)
    templates_glob = join(templates_directory, '**', templates_matcher)
    return glob(templates_glob, recursive=True)


@manager.command
def devserver():
    templates_paths = _templates_paths_for('*.html')
    reload_server_if_changed = templates_paths

    app.run(debug=True, extra_files=reload_server_if_changed)  # nosec


@manager.command
def resetdb():
    remove(AppConfig.LOCAL_EMAIL_STORE)
    remove(AppConfig.SQLITE_PATH)


@manager.option('-n', '--name', required=True)
@manager.option('-p', '--password', required=True)
def createadmin(name, password):
    email = '{}@{}'.format(name, AppConfig.CLIENT_EMAIL_HOST)

    user = user_datastore.find_user(email=email)
    if user is None:
        user = user_datastore.create_user(email=email)

    user.reset_password(password)
    user.make_admin()
    user.save()


if __name__ == '__main__':
    manager.run()
