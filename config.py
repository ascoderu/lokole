# -*- coding: utf-8 -*-
import os

from flask_babel import lazy_gettext as _

basedir = os.path.abspath(os.path.dirname(__file__))

LANGUAGES = {
    'en': 'English',
    'it': 'Italiano',
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
        'email_done': _('Email sent!'),
        'email_delayed': _('Email will be sent soon!'),
        'flash_error': _('Error'),
        'flash_info': _('Information'),
        'flash_success': _('Success'),
        'unauthorized': _('You do not have permission to view this page.'),
        'login': _('Login'),
        'logout': _('Logout'),
        'register': _('Register'),
        'opwen': _('Opwen'),
        'show_menu': _('Toggle navigation'),
        'sync': _('Sync now!'),
        'home': _('Home'),
        'about': _('About'),
        'email': _('Email'),
        'email_new': _('Write new'),
        'email_inbox': _('Inbox'),
        'email_sent': _('Sent'),
        'email_outbox': _('Outbox'),
        'email_empty': _('No emails.'),
        'not_registered': _("Don't have an account?"),
        'register_now': _('Register now!'),
        'password_field': _('Password'),
        'password_field_too_short': _('Password must be at least 6 characters'),
        'password_field_invalid': _('Invalid password'),
        'password_field_required': _('Please provide a password'),
        'password_field_must_match': _('Password does not match'),
        'password_confirm_field': _('Retype password'),
        'welcome_user': _('Welcome, %(user)s!', **kwargs),
        'welcome_back_user': _('Welcome back, %(user)s!', **kwargs),
        'loggedout_user': _('Logged out successfully!'),
        'login_required': _('Please log in to access this page.'),
        'download_complete': _('Downloaded %(num)d emails.', **kwargs),
        'upload_complete': _('Uploaded %(num)d emails.', **kwargs),
    }[key]


class Config(object):
    TESTING = False

    ADMIN_ROLE = 'admininstrator'
    ADMIN_NAME = 'opwen-administrator'
    ADMIN_PASSWORD = 'OPWEN: emails 4 the world!'

    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'opwen.db')
    SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    EMAILS_PER_PAGE = 20

    CLIENT_NAME = os.getenv('OPWEN_CLIENT_NAME')

    REMOTE_STORAGE_CLASS = 'utils.remote_storage.AzureBlob'
    REMOTE_STORAGE_ACCOUNT_NAME = os.getenv('OPWEN_REMOTE_ACCOUNT_NAME')
    REMOTE_STORAGE_ACCOUNT_KEY = os.getenv('OPWEN_REMOTE_ACCOUNT_KEY')
    REMOTE_STORAGE_CONTAINER = 'opwen'
    REMOTE_UPLOAD_PATH = '%s/from_opwen/new' % CLIENT_NAME
    REMOTE_UPLOAD_FORMAT = '%Y-%m-%d_%H-%M.json.gz'
    REMOTE_DOWNLOAD_PATH = '%s/to_opwen/new.json.gz' % CLIENT_NAME
    REMOTE_SERIALIZATION_CLASS = 'utils.serialization.CompressedJson'
    REMOTE_PACKER_CLASS = 'opwen_webapp.models.ModelPacker'

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
    SECURITY_MSG_LOGIN = ui('login_required'), 'error'
    SECURITY_MSG_UNAUTHORIZED = ui('unauthorized'), 'error'
    SECURITY_MSG_PASSWORD_MISMATCH = ui('password_field_must_match'), 'error'
    SECURITY_MSG_RETYPE_PASSWORD_MISMATCH = ui('password_field_must_match'), 'error'
    SECURITY_MSG_PASSWORD_NOT_PROVIDED = ui('password_field_required'), 'error'
    SECURITY_MSG_INVALID_PASSWORD = ui('password_field_invalid'), 'error'
    SECURITY_MSG_PASSWORD_INVALID_LENGTH = ui('password_field_too_short'), 'error'
