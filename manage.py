#!/usr/bin/env python3

from flask_migrate import MigrateCommand
from flask_script import Manager

from ca.ascoderu.lokole.infrastructure.management import BabelCommand
from ca.ascoderu.lokole.web import app

manager = Manager(app)
manager.add_command('db', MigrateCommand)
manager.add_command('babel', BabelCommand)

manager.run()
