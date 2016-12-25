# pylint: disable=no-member

from flask_migrate import Migrate
from flask_security import LoginForm as _LoginForm
from flask_security import RegisterForm as _RegisterForm
from flask_security import RoleMixin
from flask_security import SQLAlchemyUserDatastore
from flask_security import Security
from flask_security import UserMixin
from flask_security import login_required as _login_required
from flask_security import roles_required
from flask_security.forms import email_required
from flask_security.forms import email_validator
from flask_security.forms import unique_user_email
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import OperationalError
from wtforms.validators import Regexp

from opwen_infrastructure.wtforms import SuffixedStringField

from opwen_email_client import app
from opwen_email_client.config import AppConfig
from opwen_email_client.config import i8n

_db = SQLAlchemy(app)

_roles_users = _db.Table(
    'roles_users',
    _db.Column('user_id', _db.Integer(), _db.ForeignKey('user.id')),
    _db.Column('role_id', _db.Integer(), _db.ForeignKey('role.id')))


class User(_db.Model, UserMixin):
    id = _db.Column(_db.Integer(), primary_key=True)
    email = _db.Column(_db.String(255), unique=True, index=True)
    password = _db.Column(_db.String(255), nullable=False)
    active = _db.Column(_db.Boolean(), default=True)
    last_login = _db.Column(_db.DateTime())
    roles = _db.relationship('Role', secondary=_roles_users,
                             backref=_db.backref('users', lazy='dynamic'))

    @property
    def is_admin(self):
        """
        :rtype: bool

        """
        return self.has_role('admin')

    def save(self):
        _db.session.add(self)
        _db.session.commit()

    def can_access(self, email):
        """
        :type email: dict
        :rtype: bool

        """
        actors = set()
        actors.add(email.get('from'))
        actors.update(email.get('to', []))
        actors.update(email.get('cc', []))
        actors.update(email.get('bcc', []))

        return self.email in actors


class Role(_db.Model, RoleMixin):
    id = _db.Column(_db.Integer(), primary_key=True)
    name = _db.Column(_db.String(32), unique=True)
    description = _db.Column(_db.String(255))


# pylint: disable=too-many-ancestors
# noinspection PyClassHasNoInit
class LoginForm(_LoginForm):
    email = SuffixedStringField(
        suffix='@{}'.format(AppConfig.CLIENT_EMAIL_HOST))


# pylint: disable=too-many-ancestors
# noinspection PyClassHasNoInit
class RegisterForm(_RegisterForm):
    email = SuffixedStringField(
        suffix='@{}'.format(AppConfig.CLIENT_EMAIL_HOST),
        validators=[Regexp('^[a-zA-Z0-9-.@]*$', message=i8n.EMAIL_CHARACTERS),
                    email_required, email_validator, unique_user_email])


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
    if app.config.get('TESTING'):
        return func

    return _login_required(func)


def admin_required(func):
    if app.config.get('TESTING'):
        return func

    return roles_required(admin_role)(func)
