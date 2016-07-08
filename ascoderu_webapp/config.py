# -*- coding: utf-8 -*-
import os


basedir = os.path.abspath(os.path.dirname(__file__))

LANGUAGES = {
    'en': 'English',
}

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'ascoderu.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = False
