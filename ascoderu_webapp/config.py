# -*- coding: utf-8 -*-
import os


basedir = os.path.abspath(os.path.dirname(__file__))

LANGUAGES = {
    'en': 'English',
}

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'ascoderu.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = False

SECRET_KEY = 's3cr3t'

SECURITY_USER_IDENTITY_ATTRIBUTES = ('name', 'email')
SECURITY_PASSWORD_HASH = 'bcrypt'
SECURITY_PASSWORD_SALT = 'password-salt'
SECURITY_REGISTERABLE = True
SECURITY_SEND_REGISTER_EMAIL = False
SECURITY_LOGIN_USER_TEMPLATE = 'login.html'
SECURITY_REGISTER_USER_TEMPLATE = 'register.html'
