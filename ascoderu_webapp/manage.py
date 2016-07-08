#!/usr/bin/env python3

from flask_script import Manager
from flask_migrate import MigrateCommand

from ascoderu_webapp import app

manager = Manager(app)
manager.add_command('db', MigrateCommand)

manager.run()
