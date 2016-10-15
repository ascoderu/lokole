from os import getenv
from os import path
from tempfile import gettempdir

from flask_babel import gettext as _

state_basedir = path.abspath(getenv('OPWEN_STATE_DIRECTORY', gettempdir()))


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
    LOKOLE_TEAM = _('Lokole Team')
    WELCOME = _('Welcome!')
    ACCOUNT_CREATED = _('Your Lokole account has been created successfully!')
    SYNC_COMPLETE = _('Email synchronization completed.')


class FlaskConfig(object):
    SQLITE_PATH = path.join(state_basedir, 'app.sqlite3')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + SQLITE_PATH
    SQLALCHEMY_MIGRATE_REPO = path.join(state_basedir, 'app.migrate')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = getenv('OPWEN_SECRET_KEY', 'NonSecret')
    SECURITY_USER_IDENTITY_ATTRIBUTES = 'email'
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_PASSWORD_SALT = getenv('OPWEN_PASSWORD_SALT', 'UnSalted')
    SECURITY_REGISTERABLE = True
    SECURITY_POST_REGISTER_VIEW = 'register_complete'
    SECURITY_POST_LOGIN_VIEW = 'login_complete'
    SECURITY_POST_LOGOUT_VIEW = 'logout_complete'
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_LOGIN_USER_TEMPLATE = 'login.html'
    SECURITY_REGISTER_USER_TEMPLATE = 'register.html'
    SECURITY_MSG_LOGIN = i8n.LOGIN_REQUIRED, 'error'
    SECURITY_MSG_UNAUTHORIZED = i8n.UNAUTHORIZED, 'error'
    SECURITY_MSG_INVALID_PASSWORD = i8n.INVALID_PASSWORD, 'error'
    SECURITY_MSG_PASSWORD_INVALID_LENGTH = i8n.SHORT_PASSWORD, 'error'

    TESTING = getenv('OPWEN_ENABLE_DEBUG', False)


class UiConfig(object):
    EMAILS_PER_PAGE = 30
