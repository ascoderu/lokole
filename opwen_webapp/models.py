from datetime import datetime

from bleach import ALLOWED_TAGS
from bleach import clean
from flask_security import RoleMixin
from flask_security import UserMixin
from sqlalchemy_utils import ScalarListType

from opwen_webapp import db
from utils.strings import normalize_caseless

roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


_HEADERS = ['h%d' % i for i in range(1, 7)]
_KEEP_TAGS = ALLOWED_TAGS + _HEADERS + ['u']


def _normalize(data, keep_case=False):
    """
    :type data: str
    :type keep_case: bool
    :rtype: str

    """
    data = clean(data, strip=True, tags=_KEEP_TAGS)

    if not keep_case:
        data = normalize_caseless(data)
    return data


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
        super().__init__(
            email=_normalize(email),
            name=_normalize(name),
            **kwargs)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class Email(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    date = db.Column(db.DateTime(timezone=True))
    sender = db.Column(db.String(255), nullable=False)
    to = db.Column(ScalarListType(), nullable=False)
    subject = db.Column(db.String())
    body = db.Column(db.String())

    def __init__(self, to=None, sender=None, subject=None, body=None, **kwargs):
        super().__init__(
            to=[_normalize(recipient) for recipient in to] if to else to,
            sender=_normalize(sender),
            subject=_normalize(subject, keep_case=True),
            body=_normalize(body, keep_case=True),
            **kwargs)

    def is_complete(self):
        return (self.sender and
                self.to and
                self.date and
                (self.subject or self.body))

    def is_same_as(self, other):
        """
        :type other: Email
        :rtype: bool

        """
        return (isinstance(other, Email) and
                other.sender == self.sender and
                other.subject == self.subject and
                other.body == self.body and
                ((other.date is None and self.date is None) or
                 (abs(other.date - self.date).seconds < 60)) and
                set(other.to) == set(self.to))


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
