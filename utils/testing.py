from datetime import datetime

from ascoderu_webapp import app
from ascoderu_webapp import db
from ascoderu_webapp.models import Email
from ascoderu_webapp.models import User
from config import Config


# noinspection PyUnusedLocal
class DummyRemoteStorage(object):
    def __init__(self, *args, **kwargs):
        self.downloaded = kwargs.pop('download', None)
        self.uploaded = []

    def upload(self, payload):
        self.uploaded.append(payload)

    def download(self):
        return self.downloaded


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


# noinspection PyPep8Naming,PyMethodMayBeStatic,PyArgumentList
class AppTestMixin(object):
    DEFAULT_EMAIL_TO = ['to@test.net']
    DEFAULT_EMAIL_SENDER = 'from@test.net'
    DEFAULT_USER_PASSWORD = 'test'

    def create_app(self):
        app.config.from_object(TestConfig)
        app.remote_storage = DummyRemoteStorage()
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def new_user(self, **kwargs):
        kwargs.setdefault('password', self.DEFAULT_USER_PASSWORD)
        user = User(**kwargs)
        db.session.add(user)
        db.session.commit()
        return user

    def new_email(self, **kwargs):
        kwargs.setdefault('to', self.DEFAULT_EMAIL_TO)
        kwargs.setdefault('sender', self.DEFAULT_EMAIL_SENDER)
        email = Email(**kwargs)
        db.session.add(email)
        db.session.commit()
        return email

    @classmethod
    def create_complete_email(cls, now=None):
        return Email(
            to=['recipient@test.net'],
            sender='sender@test.net',
            date=now or datetime.utcnow(),
            subject='subject',
            body='body')
