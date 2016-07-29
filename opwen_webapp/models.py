from datetime import datetime
from os import path

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

    attachment_relationship = db.relationship(
        'Attachment',
        backref=db.backref('email'))

    to_relationship = db.relationship(
        'Addressee', secondary=emails_addressees,
        backref=db.backref('emails', lazy='dynamic'))

    def __init__(self, to=None, sender=None, subject=None, body=None,
                 attachments=None, **kwargs):
        super().__init__(
            to_relationship=Addressee.get_or_create_all(to),
            attachment_relationship=self._setup_attachments(attachments),
            sender=make_safe(sender),
            subject=make_safe(subject, keep_case=True),
            body=make_safe(body, keep_case=True),
            **kwargs)

    @classmethod
    def _setup_attachments(cls, attachments):
        return [Attachment(name=path.basename(filepath), path=filepath)
                for filepath in attachments or []]

    @property
    def attachments(self):
        """
        :rtype: list[str]

        """
        return [attachment.path for attachment in self.attachment_relationship]

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


class ModelPacker(object):
    _accounts_container = 'accounts'
    _field_name = 'name'
    _field_email = 'email'

    _emails_container = 'emails'
    _field_date = 'date'
    _field_to = 'to'
    _field_sender = 'sender'
    _field_subject = 'subject'
    _field_body = 'body'

    _date_format = '%Y-%m-%d %H:%M'

    @classmethod
    def _format_date(cls, utcdatetime):
        """
        :type utcdatetime: datetime
        :rtype: str

        """
        if not utcdatetime:
            return None
        return utcdatetime.strftime(cls._date_format)

    @classmethod
    def _parse_date(cls, datestring):
        """
        :type datestring: str
        :rtype: datetime

        """
        if not datestring:
            return None
        return datetime.strptime(datestring, cls._date_format)

    @classmethod
    def pack(cls, emails):
        """
        :type emails: collections.Iterable[models.Email]
        :rtype: dict[str,list[dict[str,str]]]

        """
        return {
            cls._emails_container: [{
                cls._field_date: cls._format_date(email.date),
                cls._field_to: email.to,
                cls._field_sender: email.sender,
                cls._field_subject: email.subject,
                cls._field_body: email.body,
            } for email in emails],
        }

    @classmethod
    def unpack_emails(cls, packed):
        """
        :type packed: dict[str,object]
        :rtype: list[models.Email]

        """
        if not packed:
            return []

        return [Email(
            date=cls._parse_date(email.get(cls._field_date)),
            to=email.get(cls._field_to),
            sender=email.get(cls._field_sender),
            subject=email.get(cls._field_subject),
            body=email.get(cls._field_body))
            for email in packed.get(cls._emails_container, [])]

    @classmethod
    def unpack_accounts(cls, packed):
        """
        :type packed: dict[str,object]
        :rtype: list[models.User]

        """
        if not packed:
            return []

        return [(account.get(cls._field_name), account.get(cls._field_email))
                for account in packed.get(cls._accounts_container, [])]
