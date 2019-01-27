from datetime import timedelta
from functools import wraps
from typing import Optional

from flask import request
from flask_migrate import Migrate
from flask_security import LoginForm as _LoginForm
from flask_security import RegisterForm as _RegisterForm
from flask_security import RoleMixin
from flask_security import Security
from flask_security import SQLAlchemyUserDatastore
from flask_security import UserMixin
from flask_security import login_required as _login_required
from flask_security import roles_required
from flask_security.forms import email_required
from flask_security.forms import email_validator
from flask_security.forms import unique_user_email
from flask_security.utils import hash_password
from flask_sqlalchemy import SQLAlchemy
from passlib.pwd import genword
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import OperationalError
from wtforms import IntegerField
from wtforms.validators import NoneOf
from wtforms.validators import Regexp

from opwen_email_client.util.wtforms import SuffixedStringField
from opwen_email_client.webapp import app
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.config import i8n

_db = SQLAlchemy(app)

# noinspection PyUnresolvedReferences
_roles_users = _db.Table(
    'roles_users',
    _db.Column('user_id', _db.Integer(), _db.ForeignKey('user.id')),
    _db.Column('role_id', _db.Integer(), _db.ForeignKey('role.id')))


# noinspection PyUnresolvedReferences
class User(_db.Model, UserMixin):
    id = _db.Column(_db.Integer(), primary_key=True)
    email = _db.Column(_db.String(255), unique=True, index=True)
    password = _db.Column(_db.String(255), nullable=False)
    active = _db.Column(_db.Boolean(), default=True)
    last_login_at = _db.Column(_db.DateTime())
    current_login_at = _db.Column(_db.DateTime())
    last_login_ip = _db.Column(_db.String(128))
    current_login_ip = _db.Column(_db.String(128))
    login_count = _db.Column(_db.Integer())
    timezone_offset_minutes = _db.Column(_db.Integer(), nullable=False,
                                         default=0)
    language = _db.Column(_db.String(8))
    roles = _db.relationship('Role', secondary=_roles_users,
                             backref=_db.backref('users', lazy='dynamic'))

    @property
    def is_admin(self) -> bool:
        return self.has_role('admin')

    def make_admin(self):
        user_datastore.add_role_to_user(self, admin_role)

    def reset_password(self, password: Optional[str] = None) -> str:
        new_password = password or genword()
        self.password = hash_password(new_password)
        return new_password

    def format_last_login(self, timezone_offset_minutes) -> str:
        if not self.last_login_at:
            return ''

        date = self.last_login_at - timedelta(minutes=timezone_offset_minutes)
        return date.strftime('%Y-%m-%d %H:%M')

    def save(self):
        _db.session.add(self)
        _db.session.commit()

    def can_access(self, email: dict) -> bool:
        actors = set()
        actors.add(email.get('from'))
        actors.update(email.get('to', []))
        actors.update(email.get('cc', []))
        actors.update(email.get('bcc', []))

        return self.email in actors


# noinspection PyUnresolvedReferences
class Role(_db.Model, RoleMixin):
    id = _db.Column(_db.Integer(), primary_key=True)
    name = _db.Column(_db.String(32), unique=True)
    description = _db.Column(_db.String(255))


# noinspection PyClassHasNoInit
class LoginForm(_LoginForm):
    email = SuffixedStringField(
        suffix='@{}'.format(AppConfig.CLIENT_EMAIL_HOST))


email_character_validator = Regexp(
    '^[a-zA-Z0-9-.@]*$', message=i8n.EMAIL_CHARACTERS)

forbidden_account_validator = NoneOf(
    AppConfig.FORBIDDEN_ACCOUNTS, message=i8n.FORBIDDEN_ACCOUNT)


# noinspection PyClassHasNoInit
class RegisterForm(_RegisterForm):
    email = SuffixedStringField(
        suffix='@{}'.format(AppConfig.CLIENT_EMAIL_HOST),
        validators=[email_character_validator, forbidden_account_validator,
                    email_required, email_validator, unique_user_email])

    timezone_offset_minutes = IntegerField(default=0)


user_datastore = SQLAlchemyUserDatastore(_db, User, Role)

try:
    _db.create_all()
except OperationalError:
    pass

Migrate(app, _db)
Security(app, user_datastore, register_form=RegisterForm, login_form=LoginForm)

admin_role = 'admin'
user_datastore.find_or_create_role(name=admin_role)

try:
    user_datastore.commit()
except IntegrityError:
    user_datastore.db.session.rollback()


def login_required(func):
    if AppConfig.TESTING:
        return func

    return _login_required(func)


def admin_required(func):
    if AppConfig.TESTING:
        return func

    if AppConfig.ADMIN_SECRET:
        @wraps(func)
        def decorated_view(*args, **kwargs):
            secret = request.args.get('secret')
            if secret == AppConfig.ADMIN_SECRET:
                return func(*args, **kwargs)
            return roles_required(admin_role)(func)(*args, **kwargs)
        return decorated_view

    return roles_required(admin_role)(func)
