from logging import ERROR
from os import path
from tempfile import gettempdir

from babel import Locale
from flask_babel import gettext as _

from opwen_email_client.util.os import getenv
from opwen_email_client.util.os import subdirectories


state_basedir = path.abspath(getenv('OPWEN_STATE_DIRECTORY', gettempdir()))
app_basedir = path.abspath(path.dirname(__file__))


# noinspection PyPep8Naming
class i8n(object):
    LOGIN_REQUIRED = _('Please log in to access this page.')
    UNAUTHORIZED = _('You do not have permission to view this page.')
    INVALID_PASSWORD = _('Invalid password.')
    SHORT_PASSWORD = _('The password must have at least 6 characters.')
    EMAIL_SENT = _('Email sent!')
    EMAIL_ADDRESS_INVALID = _('Invalid email address.')
    EMAIL_TO_REQUIRED = _('Please specify a recipient.')
    LOGGED_IN = _('You are now logged in.')
    LOGGED_OUT = _('You have logged out successfully.')
    WELCOME = _('Welcome!')
    EMAIL_CHARACTERS = _('Please only use letters, numbers, dots and dashes.')
    ACCOUNT_CREATED = _('Your Lokole account has been created successfully!')
    ACCOUNT_SUSPENDED = _('Your account has been suspended. '
                          'Please contact your administrator.')
    SYNC_COMPLETE = _('Email synchronization completed.')
    UNEXPECTED_ERROR = _('Unexpected error. Please contact your admin.')
    PAGE_DOES_NOT_EXIST = _('This page does not exist.')
    USER_DOES_NOT_EXIST = _('This user does not exist.')
    USER_SUSPENDED = _('The user was suspended.')
    USER_UNSUSPENDED = _('The user was un-suspended.')
    ADMIN_CANNOT_BE_SUSPENDED = _("Administrators can't be suspended.")
    PASSWORD_CHANGED_BY_ADMIN = _('Password was reset by administrator to: ')
    SAME_PASSWORD = _(' Your new password must be different than your '
                      'previous password.')


class AppConfig(object):
    SQLITE_PATH = path.join(state_basedir, 'users.sqlite3')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + SQLITE_PATH
    SQLALCHEMY_MIGRATE_REPO = path.join(state_basedir, 'app.migrate')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ADMIN_SECRET = getenv('OPWEN_ADMIN_SECRET')
    SECRET_KEY = getenv('OPWEN_SESSION_KEY')
    SECURITY_USER_IDENTITY_ATTRIBUTES = 'email'
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_PASSWORD_SALT = getenv('OPWEN_PASSWORD_SALT')
    SECURITY_REGISTERABLE = True
    SECURITY_CHANGEABLE = True
    SECURITY_TRACKABLE = True
    SECURITY_SEND_PASSWORD_CHANGE_EMAIL = False
    SECURITY_POST_REGISTER_VIEW = 'register_complete'
    SECURITY_POST_LOGIN_VIEW = 'login_complete'
    SECURITY_POST_LOGOUT_VIEW = 'logout_complete'
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_MSG_LOGIN = i8n.LOGIN_REQUIRED, 'error'
    SECURITY_MSG_UNAUTHORIZED = i8n.UNAUTHORIZED, 'error'
    SECURITY_MSG_INVALID_PASSWORD = i8n.INVALID_PASSWORD, 'error'
    SECURITY_MSG_DISABLED_ACCOUNT = i8n.ACCOUNT_SUSPENDED, 'error'
    SECURITY_MSG_PASSWORD_INVALID_LENGTH = i8n.SHORT_PASSWORD, 'error'
    SECURITY_MSG_PASSWORD_IS_THE_SAME = i8n.SAME_PASSWORD, 'error'
    SECURITY_LOGIN_URL = '/user/login'
    SECURITY_LOGOUT_URL = '/user/logout'
    SECURITY_REGISTER_URL = '/user/register'
    SECURITY_CHANGE_URL = '/user/password/change'

    TESTING = getenv('OPWEN_ENABLE_DEBUG', False)

    LOCAL_EMAIL_STORE = path.join(state_basedir, 'emails.sqlite3')

    EMAIL_ADDRESS_DELIMITER = ','
    EMAILS_PER_PAGE = 30

    LOG_FORMAT = '%(asctime)s\t%(levelname)s\t%(message)s'
    LOG_LEVEL = ERROR

    LOCALES_DIRECTORY = path.join(app_basedir, 'translations')
    DEFAULT_LOCALE = Locale.parse('en_ca')
    LOCALES = (
        [DEFAULT_LOCALE] +
        [Locale.parse(code) for code in subdirectories(LOCALES_DIRECTORY)])

    EMAIL_SERVER_READ_API_HOSTNAME = getenv('OPWEN_EMAIL_SERVER_READ_API')
    EMAIL_SERVER_WRITE_API_HOSTNAME = getenv('OPWEN_EMAIL_SERVER_WRITE_API')
    EMAIL_HOST_FORMAT = '{}.lokole.ca'
    STORAGE_CONTAINER = 'compressedpackages'
    STORAGE_ACCOUNT_NAME = getenv('OPWEN_REMOTE_ACCOUNT_NAME')
    STORAGE_ACCOUNT_KEY = getenv('OPWEN_REMOTE_ACCOUNT_KEY')
    CLIENT_NAME = getenv('OPWEN_CLIENT_NAME')
    CLIENT_ID = getenv('OPWEN_CLIENT_ID')
    CLIENT_EMAIL_HOST = EMAIL_HOST_FORMAT.format(CLIENT_NAME)
