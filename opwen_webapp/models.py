from collections import namedtuple
from flask_security import RoleMixin
from flask_security import UserMixin

from opwen_webapp import db
from utils.strings import make_safe

roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

emails_addressees = db.Table(
    'emails_addressees',
    db.Column('email_id', db.Integer(), db.ForeignKey('email.id')),
    db.Column('addressee_id', db.Integer(), db.ForeignKey('addressee.id')))


# noinspection PyClassHasNoInit
class SyncReport(namedtuple('SyncReport',
                            'emails_uploaded emails_downloaded')):
    pass


class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(255), unique=True, index=True)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean(), default=True)

    name = db.Column(db.String(255), unique=True, index=True)

    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    # noinspection PyArgumentList
    def __init__(self, email=None, name=None, **kwargs):
        email = make_safe(email)
        name = make_safe(name)
        super().__init__(
            email=email or name,
            name=name or email,
            **kwargs)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class Attachment(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(255), nullable=False)

    email_id = db.Column(db.Integer(), db.ForeignKey('email.id'))


class Addressee(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    val = db.Column(db.String(255), unique=True, nullable=False, index=True)

    @classmethod
    def get_or_create(cls, name_or_email):
        # FIXME: this is not thread safe
        name_or_email = make_safe(name_or_email)
        instance = Addressee.query.filter_by(val=name_or_email).first()
        if not instance:
            instance = Addressee(val=name_or_email)
            db.session.add(instance)
            db.session.commit()
        return instance

    @classmethod
    def get_or_create_all(cls, names_or_emails):
        if not names_or_emails:
            return names_or_emails
        return [cls.get_or_create(to) for to in names_or_emails]


class Email(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    date = db.Column(db.DateTime(timezone=True))
    sender = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String())
    body = db.Column(db.String())

    attachments = db.relationship(
        'Attachment',
        backref=db.backref('email'))

    to_relationship = db.relationship(
        'Addressee', secondary=emails_addressees,
        backref=db.backref('emails', lazy='dynamic'))

    def __init__(self, to=None, sender=None, subject=None, body=None,
                 attachments=None, **kwargs):
        super().__init__(
            to_relationship=Addressee.get_or_create_all(to),
            attachments=self._setup_attachments(attachments),
            sender=make_safe(sender),
            subject=make_safe(subject, keep_case=True),
            body=make_safe(body, keep_case=True),
            **kwargs)

    @classmethod
    def _setup_attachments(cls, attachments):
        return [Attachment(path=path, name=name)
                for path, name in attachments or []]

    @property
    def to(self):
        """
        :rtype: list[str]

        """
        return [addressee.val for addressee in self.to_relationship]

    def is_complete(self):
        """
        :rtype: bool

        """
        return (self.sender and
                self.to and
                self.date and
                (self.subject or self.body))

    def is_same_as(self, other):
        """
        :type other: Email
        :rtype: bool

        """
        try:
            return (other.sender == self.sender and
                    other.subject == self.subject and
                    other.body == self.body and
                    ((other.date is None and self.date is None) or
                     (abs(other.date - self.date).seconds < 60)) and
                    set(other.to) == set(self.to))
        except AttributeError:
            return False
