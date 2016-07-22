# -*- coding: utf-8 -*-
import os

from flask_babel import lazy_gettext as _

basedir = os.path.abspath(os.path.dirname(__file__))

LANGUAGES = {
    'en': 'English',
}


def ui(key, **kwargs):
    return {
        'email_field': _('Name or Email'),
        'email_field_required': _('Please enter your name or email.'),
        'name_field': _('Name'),
        'name_field_required': _('Please enter your name.'),
        'name_field_already_exists': _('Sorry, this name is already in use.'),
        'email_to_field': _('To'),
        'email_to_field_required': _('Please specify a recipient.'),
        'email_to_field_invalid': _('Must be a user name or email address.'),
        'email_subject_field': _('Subject'),
        'email_body_field': _('Message'),
        'email_submit_field': _('Send'),
        'email_sent': _('Email sent!'),
        'email_delayed': _('Email will be sent soon!'),
        'welcome_user': _('Welcome, %(user)s!', **kwargs),
        'welcome_back_user': _('Welcome back, %(user)s!', **kwargs),
        'loggedout_user': _('Logged out successfully!'),
        'download_complete': _('Downloaded %(num)d emails.', **kwargs),
        'upload_complete': _('Uploaded %(num)d emails.', **kwargs),
    }[key]


class Config(object):
    TESTING = False

    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'ascoderu.db')
    SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CLIENT_NAME = 'dev-cw'

    REMOTE_STORAGE_CLASS = 'utils.remote_storage.AzureBlob'
    REMOTE_STORAGE_ACCOUNT_NAME = 'clewolff'
    REMOTE_STORAGE_ACCOUNT_KEY = os.getenv('ASCODERU_REMOTE_ACCOUNT_KEY')
    REMOTE_STORAGE_CONTAINER = 'ascoderu'
    REMOTE_UPLOAD_PATH = '%s/from_opwen/new' % CLIENT_NAME
    REMOTE_UPLOAD_FORMAT = '%Y-%m-%d_%H-%M.json.gz'
    REMOTE_DOWNLOAD_PATH = '%s/to_opwen/new.json.gz' % CLIENT_NAME
    REMOTE_SERIALIZATION_CLASS = 'utils.serialization.CompressedJson'
    REMOTE_PACKER_CLASS = 'ascoderu_webapp.models.ModelPacker'

    SECRET_KEY = 's3cr3t'

    SECURITY_USER_IDENTITY_ATTRIBUTES = ('name', 'email')
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_PASSWORD_SALT = 'password-salt'
    SECURITY_REGISTERABLE = True
    SECURITY_POST_REGISTER_VIEW = 'post_register'
    SECURITY_POST_LOGIN_VIEW = 'post_login'
    SECURITY_POST_LOGOUT_VIEW = 'post_logout'
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_LOGIN_USER_TEMPLATE = 'login.html'
    SECURITY_REGISTER_USER_TEMPLATE = 'register.html'
