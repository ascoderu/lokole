#!/usr/bin/env python3

from flask_migrate import MigrateCommand
from flask_script import Manager

from ascoderu_webapp import app
from utils.babel import BabelCommand

manager = Manager(app)
manager.add_command('db', MigrateCommand)
manager.add_command('babel', BabelCommand)

manager.run()
