#!/usr/bin/env python3

from flask_migrate import MigrateCommand
from flask_script import Manager

from opwen_webapp import app
from opwen_webapp.helpers.commands import BabelCommand
from opwen_webapp.helpers.commands import PopulateDatabaseWithTestEntriesCommand

manager = Manager(app)
manager.add_command('db', MigrateCommand)
manager.add_command('babel', BabelCommand)
manager.add_command('dbpopulate', PopulateDatabaseWithTestEntriesCommand)

manager.run()
