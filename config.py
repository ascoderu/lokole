# -*- coding: utf-8 -*-
import os

from flask_babel import gettext

basedir = os.path.abspath(os.path.dirname(__file__))

LANGUAGES = {
    'en': 'English',
}


def ui(key, **kwargs):
    message = {
        'email_field': 'Name or Email',
        'email_field_required': 'Please enter your name or email.',
        'name_field': 'Name',
        'name_field_required': 'Please enter your name.',
        'name_field_already_exists': 'Sorry, this name is already in use.',
        'email_to_field': 'To',
        'email_to_field_required': 'Please specify a recipient.',
        'email_to_field_invalid': 'Must be a user name or email address.',
        'email_subject_field': 'Subject',
        'email_body_field': 'Message',
        'email_submit_field': 'Send',
        'email_sent': 'Email sent!',
        'email_delayed': 'Email will be sent soon!',
        'welcome_user': 'Welcome, %(user)s!',
        'welcome_back_user': 'Welcome back, %(user)s!',
        'loggedout_user': 'Logged out successfully!',
    }[key]
    return gettext(message, **kwargs)


TESTING = False

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'ascoderu.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = False

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
