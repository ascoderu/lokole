from datetime import timedelta
from typing import Optional

from flask_migrate import Migrate
from flask_security import RoleMixin
from flask_security import SQLAlchemyUserDatastore
from flask_security import UserMixin
from flask_security.utils import hash_password
from flask_sqlalchemy import SQLAlchemy
from passlib.pwd import genword
from sqlalchemy.exc import OperationalError

from opwen_email_client.domain.email.user_store import UserStore

_db = SQLAlchemy()

# noinspection PyUnresolvedReferences
_roles_users = _db.Table(
    'roles_users',
    _db.Column('user_id', _db.Integer(), _db.ForeignKey('user.id')),
    _db.Column('role_id', _db.Integer(), _db.ForeignKey('role.id')),
)


# noinspection PyUnresolvedReferences
class _User(_db.Model, UserMixin):
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
class _Role(_db.Model, RoleMixin):
    __tablename__ = 'role'

    id = _db.Column(_db.Integer(), primary_key=True)
    name = _db.Column(_db.String(32), unique=True)
    description = _db.Column(_db.String(255))


_migrate = Migrate()


class FlaskLoginUserStore(UserStore):
    def __init__(self):
        self.datastore = SQLAlchemyUserDatastore(_db, _User, _Role)
        self.app = None

    def init_app(self, app):
        self.app = app
        self._init_datastore()

    def _init_datastore(self):
        with self.app.app_context():
            _db.init_app(self.app)
            _migrate.init_app(self.app, _db)

            try:
                _db.create_all()
            except OperationalError:
                pass

    def fetch_one(self, userid):
        with self.app.app_context():
            return _User.query.filter_by(id=userid).first()

    def fetch_all(self):
        with self.app.app_context():
            return _User.query.all()

    def fetch_pending(self):
        with self.app.app_context():
            return _User.query.filter_by(synced=False).all()

    def mark_as_synced(self, users):
        with self.app.app_context():
            for user in users:
                user.synced = True
                _db.session.add(user)
            _db.session.commit()

    def make_admin(self, user):
        with self.app.app_context():
            user.is_admin = True
            user.save()

    def create_if_not_exists(self, email):
        with self.app.app_context():
            user = self.datastore.find_user(email=email)
            if user is None:
                user = self.datastore.create_user(email=email, password='')  # nosec

            return user
