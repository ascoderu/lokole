from collections import namedtuple
from datetime import datetime

from config import Config
from opwen_webapp import app
from opwen_webapp import db
from opwen_webapp import security
from opwen_webapp.models import Email
from opwen_webapp.models import User


# noinspection PyUnusedLocal
class DummyRemoteStorage(object):
    def __init__(self, *args, download=None, **kwargs):
        """
        :type download: bytes

        """
        self.downloaded = download
        self.uploaded = []

    def upload(self, payload):
        """
        :type payload: bytes

        """
        self.uploaded.append(payload)

    def download(self):
        return self.downloaded


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SECRET_KEY = 's3cr3t'
    SECURITY_PASSWORD_SALT = 'password-salt'


# noinspection PyPep8Naming,PyMethodMayBeStatic,PyArgumentList
class AppTestMixin(object):
    _email = namedtuple('Email', ('to', 'sender', 'date', 'subject', 'body'))

    def create_app(self):
        app.config.from_object(TestConfig)
        app.remote_storage = DummyRemoteStorage()
        security.init_app(app, register_blueprint=False)
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def new_user(self, password='test', **kwargs):
        """
        :type password: str

        """
        user = User(password=password, **kwargs)
        db.session.add(user)
        db.session.commit()
        return user

    def new_email(self, sender='from@test.net', to=('to@test.net',), **kwargs):
        """
        :type sender: str
        :type to: list[str]

        """
        email = Email(sender=sender, to=to, **kwargs)
        db.session.add(email)
        db.session.commit()
        return email

    @classmethod
    def create_complete_email_fake(cls, **kwargs):
        return cls._email(
            to=kwargs.get('to', ['recipient@test.net']),
            sender=kwargs.get('sender', 'sender@test.net'),
            date=kwargs.get('date', datetime.utcnow()),
            subject=kwargs.get('subject', 'the subject'),
            body=kwargs.get('body', 'the body'))

    @classmethod
    def create_complete_email(cls, **kwargs):
        """
        :rtype: Email

        """
        return Email(
            to=kwargs.get('to', ['recipient@test.net']),
            sender=kwargs.get('sender', 'sender@test.net'),
            date=kwargs.get('date', datetime.utcnow()),
            subject=kwargs.get('subject', 'the subject'),
            body=kwargs.get('body', 'the body'))
