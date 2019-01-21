from os import path
from tempfile import gettempdir

from babel import Locale
from dotenv import load_dotenv
from flask_babelex import gettext as _

from opwen_email_client.util.os import getenv
from opwen_email_client.util.os import subdirectories

settings_path = getenv('OPWEN_SETTINGS')
load_dotenv(settings_path)

app_basedir = path.abspath(path.dirname(__file__))
root_domain = getenv('OPWEN_ROOT_DOMAIN', 'lokole.ca')


# noinspection PyPep8Naming
class i8n(object):
    SETTINGS_UPDATED = _('Settings updated! If required, the app will '
                         'restart soon to reflect the changes.')
    LOGIN_REQUIRED = _('Please log in to access this page.')
    UNAUTHORIZED = _('You do not have permission to view this page.')
    INVALID_PASSWORD = _('Invalid password.')
    SHORT_PASSWORD = _('The password must have at least 6 characters.')
    EMAIL_SENT = _('Email sent!')
    EMAIL_ADDRESS_INVALID = _('Invalid email address.')
    EMAIL_TO_REQUIRED = _('Please specify a recipient.')
    EMAIL_NO_SUBJECT = _('(no subject)')
    LOGGED_IN = _('You are now logged in.')
    LOGGED_OUT = _('You have logged out successfully.')
    WELCOME = _('Welcome!')
    EMAIL_CHARACTERS = _('Please only use letters, numbers, dots and dashes.')
    FORBIDDEN_ACCOUNT = _('This account name is not available.')
    ACCOUNT_CREATED = _('Your Lokole account has been created successfully!')
    ACCOUNT_SUSPENDED = _('Your account has been suspended. '
                          'Please contact your administrator.')
    SYNC_COMPLETE = _('Email synchronization completed.')
    UNEXPECTED_ERROR = _('Unexpected error. Please contact your '
                         'administrator.')
    PAGE_DOES_NOT_EXIST = _('This page does not exist.')
    USER_DOES_NOT_EXIST = _('This user does not exist.')
    USER_SUSPENDED = _('The user was suspended.')
    USER_UNSUSPENDED = _('The user was un-suspended.')
    USER_PROMOTED = _('The user now is an administrator.')
    ALREADY_PROMOTED = _('The user already is an administrator.')
    ADMIN_CANNOT_BE_SUSPENDED = _("Administrators can't be suspended.")
    ADMIN_PASSWORD_CANNOT_BE_RESET = _("Administrator password can't be "
                                       "reset.")
    PASSWORD_CHANGED_BY_ADMIN = _('Password was reset by administrator to: ')
    SAME_PASSWORD = _(' Your new password must be different than your '
                      'previous password.')


class AppConfig(object):
    STATE_BASEDIR = path.abspath(getenv('OPWEN_STATE_DIRECTORY', gettempdir()))
    SQLITE_PATH = path.join(STATE_BASEDIR, 'users.sqlite3')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + SQLITE_PATH
    SQLALCHEMY_MIGRATE_REPO = path.join(STATE_BASEDIR, 'app.migrate')
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

    MODEM_CONFIG_DIR = path.join(STATE_BASEDIR, 'usb_modeswitch')
    SIM_CONFIG_DIR = path.join(STATE_BASEDIR, 'wvdial')
    LOCAL_EMAIL_STORE = path.join(STATE_BASEDIR, 'emails.sqlite3')
    SIM_TYPE = getenv('OPWEN_SIM_TYPE')
    RESTART_PATH = getenv('OPWEN_RESTART_PATH')

    EMAIL_ADDRESS_DELIMITER = ','
    EMAILS_PER_PAGE = 30

    LOCALES_DIRECTORY = path.join(app_basedir, 'translations')
    DEFAULT_LOCALE = Locale.parse('en_ca')
    LOCALES = (
        [DEFAULT_LOCALE] +
        [Locale.parse(code) for code in subdirectories(LOCALES_DIRECTORY)])

    COMPRESSION = getenv('OPWEN_COMPRESSION', 'zstd')
    EMAIL_SERVER_HOSTNAME = getenv('OPWEN_EMAIL_SERVER_HOSTNAME')
    EMAIL_HOST_FORMAT = '{}.' + root_domain
    STORAGE_PROVIDER = getenv('LOKOLE_STORAGE_PROVIDER', 'AZURE_BLOBS')
    STORAGE_CONTAINER = getenv('OPWEN_REMOTE_RESOURCE_CONTAINER')
    STORAGE_ACCOUNT_NAME = getenv('OPWEN_REMOTE_ACCOUNT_NAME')
    STORAGE_ACCOUNT_KEY = getenv('OPWEN_REMOTE_ACCOUNT_KEY')
    CLIENT_NAME = getenv('OPWEN_CLIENT_NAME')
    CLIENT_ID = getenv('OPWEN_CLIENT_ID')
    CLIENT_EMAIL_HOST = EMAIL_HOST_FORMAT.format(CLIENT_NAME)
    NEWS_INBOX = 'news@{}'.format(CLIENT_EMAIL_HOST)
    ADMIN_INBOX = 'admin@{}'.format(CLIENT_EMAIL_HOST)
    NEWS_SENDERS = set(getenv('OPWEN_NEWS_SENDERS', '').split(','))
    FORBIDDEN_ACCOUNTS = [NEWS_INBOX, ADMIN_INBOX]
