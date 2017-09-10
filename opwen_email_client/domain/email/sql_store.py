from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import Text
from sqlalchemy import exists
from sqlalchemy import or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

from opwen_email_client.domain.email.store import EmailStore
from opwen_email_client.util.sqlalchemy import create_database
from opwen_email_client.util.sqlalchemy import get_or_create
from opwen_email_client.util.sqlalchemy import session

_Base = declarative_base()


_EmailTo = Table('emailto',
                 _Base.metadata,
                 Column('email_id', Integer, ForeignKey('email.id')),
                 Column('to_id', Integer, ForeignKey('to.id')))

_EmailCc = Table('emailcc',
                 _Base.metadata,
                 Column('email_id', Integer, ForeignKey('email.id')),
                 Column('cc_id', Integer, ForeignKey('cc.id')))

_EmailBcc = Table('emailbcc',
                  _Base.metadata,
                  Column('email_id', Integer, ForeignKey('email.id')),
                  Column('bcc_id', Integer, ForeignKey('bcc.id')))

_EmailAttachment = Table(
    'emailattachment',
    _Base.metadata,
    Column('email_id', Integer, ForeignKey('email.id')),
    Column('attachment_id', Integer, ForeignKey('attachment.id')))


class _To(_Base):
    __tablename__ = 'to'
    id = Column(Integer, primary_key=True)

    address = Column(String(length=128), index=True, unique=True)


class _Cc(_Base):
    __tablename__ = 'cc'
    id = Column(Integer, primary_key=True)

    address = Column(String(length=128), index=True, unique=True)


class _Bcc(_Base):
    __tablename__ = 'bcc'
    id = Column(Integer, primary_key=True)

    address = Column(String(length=128), index=True, unique=True)


class _Attachment(_Base):
    __tablename__ = 'attachment'
    id = Column(Integer, primary_key=True)

    filename = Column(Text)
    content = Column(Text)


class _Email(_Base):
    __tablename__ = 'email'
    id = Column(Integer, primary_key=True)

    uid = Column(String(length=64), unique=True, index=True)
    subject = Column(Text)
    body = Column(Text)
    sent_at = Column(DateTime())
    read = Column(Boolean, default=False, nullable=False)
    sender = Column(String(length=128), index=True)
    attachments = relationship(_Attachment, secondary=_EmailAttachment,
                               backref='emails')
    to = relationship(_To, secondary=_EmailTo)
    cc = relationship(_Cc, secondary=_EmailCc)
    bcc = relationship(_Bcc, secondary=_EmailBcc)

    def to_dict(self):
        attachments = self.attachments
        attachments = ([{'filename': attachment.filename,
                         'content': attachment.content}
                        for attachment in attachments]
                       if attachments else None)

        sent_at = self.sent_at
        sent_at = (sent_at.strftime('%Y-%m-%d %H:%M')
                   if sent_at else None)

        return {k: v for (k, v) in (
            ('from', self.sender),
            ('to', [_.address for _ in self.to]),
            ('cc', [_.address for _ in self.cc]),
            ('bcc', [_.address for _ in self.bcc]),
            ('subject', self.subject),
            ('body', self.body),
            ('_uid', self.uid),
            ('sent_at', sent_at),
            ('read', self.read),
            ('attachments', attachments),
        ) if v}

    @classmethod
    def from_dict(cls, db, email):
        sent_at = email.get('sent_at')
        sent_at = (datetime.strptime(sent_at, '%Y-%m-%d %H:%M')
                   if sent_at else None)

        return _Email(
            uid=email['_uid'],
            to=[get_or_create(db, _To, address=_.lower())
                for _ in email.get('to', [])],
            cc=[get_or_create(db, _Cc, address=_.lower())
                for _ in email.get('cc', [])],
            bcc=[get_or_create(db, _Bcc, address=_.lower())
                 for _ in email.get('bcc', [])],
            attachments=[get_or_create(db, _Attachment, **_)
                         for _ in email.get('attachments', [])],
            subject=email.get('subject'),
            body=email.get('body'),
            sent_at=sent_at,
            read=email.get('read', False),
            sender=email.get('from', '').lower() or None)

    @classmethod
    def is_sent_by(cls, email_address):
        email_address = email_address.lower()
        return cls.sender == email_address

    @classmethod
    def is_received_by(cls, email_address):
        email_address = email_address.lower()
        return (cls.to.any(_To.address == email_address) |
                cls.cc.any(_Cc.address == email_address) |
                cls.bcc.any(_Bcc.address == email_address))


class _SqlalchemyEmailStore(EmailStore):
    def __init__(self, database_uri: str):
        self._base = _Base
        self._engine = create_database(database_uri, self._base)
        self._sesion_maker = sessionmaker(autocommit=False, autoflush=False,
                                          bind=self._engine)

    def _dbread(self):
        return session(self._sesion_maker, commit=False)

    def _dbwrite(self):
        return session(self._sesion_maker, commit=True)

    def _create(self, emails):
        with self._dbwrite() as db:
            for email in emails:
                uid_exists = exists().where(_Email.uid == email['_uid'])
                if not db.query(uid_exists).scalar():
                    db.add(_Email.from_dict(db, email))

    def _mark_sent(self, uids):
        now = datetime.utcnow()
        set_sent_at = {_Email.sent_at: now}

        with self._dbwrite() as db:
            db.query(_Email)\
                .filter(_match_email_uid(uids))\
                .update(set_sent_at)

    def _mark_read(self, email_address, uids):
        set_read = {_Email.read: True}

        with self._dbwrite() as db:
            db.query(_Email)\
                .filter(_match_email_uid(uids) & _can_access(email_address))\
                .update(set_read, synchronize_session='fetch')

    def _delete(self, email_address, uids):
        should_delete = _match_email_uid(uids) & _can_access(email_address)

        with self._dbwrite() as db:
            for email in db.query(_Email).filter(should_delete).all():
                email.attachments = []
                db.delete(email)

        self._delete_orphaned_attachments()

    def _delete_orphaned_attachments(self):
        with self._dbwrite() as db:
            db.query(_Attachment)\
                .filter(~_Attachment.emails.any())\
                .delete(synchronize_session='fetch')

    def _find(self, query):
        with self._dbread() as db:
            results = db.query(_Email).filter(query)
            email = results.first()
            return email.to_dict() if email else None

    def _query(self, query):
        with self._dbread() as db:
            results = db.query(_Email).filter(query)
            for email in results.order_by(_Email.sent_at.desc()).all():
                yield email.to_dict()

    def inbox(self, email_address):
        return self._query(_Email.is_received_by(email_address))

    def outbox(self, email_address):
        return self._query(_Email.is_sent_by(email_address)
                           & _Email.sent_at.is_(None))

    def search(self, email_address, query):
        textquery = '%{}%'.format(query)
        contains_query = or_(*(_Email.subject.ilike(textquery),
                               _Email.body.ilike(textquery),
                               _Email.sender.ilike(textquery),
                               _Email.to.any(_To.address.ilike(textquery)),
                               _Email.cc.any(_Cc.address.ilike(textquery)),
                               _Email.bcc.any(_Bcc.address.ilike(textquery))))
        return self._query(_can_access(email_address) & contains_query)

    def pending(self):
        return self._query(_Email.sent_at.is_(None))

    def get(self, uid):
        return self._find(_Email.uid == uid)

    def sent(self, email_address):
        return self._query(_Email.is_sent_by(email_address)
                           & _Email.sent_at.isnot(None))


class SqliteEmailStore(_SqlalchemyEmailStore):
    def __init__(self, database_path: str):
        super().__init__('sqlite:///{}'.format(database_path))


def _can_access(email_address):
    return (_Email.is_sent_by(email_address)
            | _Email.is_received_by(email_address))


def _match_email_uid(uids):
    return or_(*(_Email.uid == uid for uid in uids))
