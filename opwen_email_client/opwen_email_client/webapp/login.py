from typing import List

from flask import Flask
from flask_migrate import Migrate
from flask_security import RoleMixin
from flask_security import SQLAlchemyUserDatastore
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from sqlalchemy.exc import OperationalError

from opwen_email_client.domain.email.user_store import User
from opwen_email_client.domain.email.user_store import UserStore
from opwen_email_client.webapp.config import AppConfig

_db = SQLAlchemy()

# noinspection PyUnresolvedReferences
_roles_users = _db.Table(
    'roles_users',
    _db.Column('user_id', _db.Integer(), _db.ForeignKey('user.id')),
    _db.Column('role_id', _db.Integer(), _db.ForeignKey('role.id')),
)


# noinspection PyUnresolvedReferences
class _User(_db.Model, User):
    __tablename__ = 'user'

    id = _db.Column(_db.Integer(), primary_key=True)
    email = _db.Column(_db.String(255), unique=True, index=True)
    password = _db.Column(_db.String(255), nullable=False)
    active = _db.Column(_db.Boolean(), default=True)
    last_login_at = _db.Column(_db.DateTime())
    current_login_at = _db.Column(_db.DateTime())
    last_login_ip = _db.Column(_db.String(128))
    current_login_ip = _db.Column(_db.String(128))
    login_count = _db.Column(_db.Integer())
    timezone_offset_minutes = _db.Column(_db.Integer(), nullable=False, default=0)
    language = _db.Column(_db.String(8))
    roles = _db.relationship('_Role', secondary=_roles_users, backref=_db.backref('users', lazy='dynamic'))
    synced = _db.Column(_db.Boolean(), default=False)
    is_admin = _db.Column(_db.Boolean(), default=False)


# noinspection PyUnresolvedReferences
class _Role(_db.Model, RoleMixin):
    __tablename__ = 'role'

    id = _db.Column(_db.Integer(), primary_key=True)
    name = _db.Column(_db.String(32), unique=True)
    description = _db.Column(_db.String(255))


_migrate = Migrate()


class FlaskLoginUserStore(UserStore):
    def __init__(self):
        store = SQLAlchemyUserDatastore(_db, _User, _Role)
        super().__init__(read=store, write=store)
        self._app = None

    def init_app(self, app: Flask):
        with app.app_context():
            _db.init_app(app)
            _migrate.init_app(app, _db)

            try:
                _db.create_all()
            except OperationalError:
                pass

        self._app = app

    def fetch_all(self, user: User) -> List[User]:
        with self._app.app_context():
            return _User.query.all()

    def fetch_pending(self) -> List[User]:
        is_not_synced = _User.synced == False  # noqa: E712
        is_non_admin = _User.email != AppConfig.ADMIN_INBOX

        with self._app.app_context():
            return _User.query\
                .filter(and_(is_not_synced, is_non_admin))\
                .all()
