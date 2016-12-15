#!/usr/bin/env python3

from flask_migrate import MigrateCommand
from flask_script import Manager

from opwen_email_client import app
from opwen_email_client.management import BabelCommand
from opwen_email_client.management import SyncDaemonCommand

manager = Manager(app)
manager.add_command('db', MigrateCommand)
manager.add_command('babel', BabelCommand)
manager.add_command('sync-daemon', SyncDaemonCommand)

manager.run()
