# -*- coding: utf-8 -*-
from os import getenv
from os import listdir
from os import path

from flask_babel import lazy_gettext as _

basedir = path.abspath(path.dirname(__file__))


def ui(key):
    return {
        'logout': _('Logout'),
        'login': _('Login'),
        'register': _('Register'),
        'sync': _('Sync now!'),
        'home': _('Home'),
        'about': _('About'),
        'email': _('Email'),
        'email_new': _('Write new'),
        'email_inbox': _('Inbox'),
        'email_sent': _('Sent'),
        'email_outbox': _('Outbox'),
    }.get(key)


class Config(object):
    DEFAULT_TRANSLATION = 'en'
    TRANSLATIONS_PATH = path.join(basedir, 'opwen_webapp', 'translations')
    TRANSLATIONS = frozenset(listdir(TRANSLATIONS_PATH) + [DEFAULT_TRANSLATION])

    TESTING = False

    ADMIN_ROLE = 'admininstrator'
    ADMIN_NAME = 'opwen-administrator'
    ADMIN_PASSWORD = 'OPWEN: emails 4 the world!'

    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + path.join(basedir, 'opwen.db')
    SQLALCHEMY_MIGRATE_REPO = path.join(basedir, 'db_repository')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_DIRECTORY = path.join(basedir, 'attachments')
    UPLOAD_ENDPOINT = 'attachments'

    EMAILS_PER_PAGE = 20

    CLIENT_NAME = getenv('OPWEN_CLIENT_NAME')

    REMOTE_STORAGE_CLASS = 'utils.remote_storage.AzureBlob'
    REMOTE_STORAGE_ACCOUNT_NAME = getenv('OPWEN_REMOTE_ACCOUNT_NAME')
    REMOTE_STORAGE_ACCOUNT_KEY = getenv('OPWEN_REMOTE_ACCOUNT_KEY')
    REMOTE_STORAGE_CONTAINER = 'opwen'
    REMOTE_UPLOAD_PATH = '%s/from_opwen/new' % CLIENT_NAME
    REMOTE_UPLOAD_FILENAME_FORMAT = '%Y-%m-%d_%H-%M.zip'
    REMOTE_DOWNLOAD_PATH = '%s/to_opwen/new.zip' % CLIENT_NAME
    REMOTE_SERIALIZER_EMAILS_NAME = 'emails.jsonl'
    REMOTE_SERIALIZER_ACCOUNTS_NAME = 'accounts.jsonl'
    REMOTE_SERIALIZER_ATTACHMENTS_NAME = 'attachments'

    MAX_CONTENT_LENGTH = 0.5 * 1024 * 1024
    SECRET_KEY = getenv('OPWEN_SECRET_KEY')

    SECURITY_USER_IDENTITY_ATTRIBUTES = ('name', 'email')
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_PASSWORD_SALT = getenv('OPWEN_PASSWORD_SALT')
    SECURITY_REGISTERABLE = True
    SECURITY_POST_REGISTER_VIEW = 'post_register'
    SECURITY_POST_LOGIN_VIEW = 'post_login'
    SECURITY_POST_LOGOUT_VIEW = 'post_logout'
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_LOGIN_USER_TEMPLATE = 'login.html'
    SECURITY_REGISTER_USER_TEMPLATE = 'register.html'
    SECURITY_MSG_LOGIN = _('Please log in to access this page.'), 'error'
    SECURITY_MSG_UNAUTHORIZED = _('You do not have permission to view this page.'), 'error'
    SECURITY_MSG_INVALID_PASSWORD = _('Invalid password'), 'error'
