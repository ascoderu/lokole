from datetime import datetime

from sqlalchemy import BLOB
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

_EmailTo = Table(
    'emailto',
    _Base.metadata,
    Column('email_id', Integer, ForeignKey('email.uid')),
    Column('to_id', Integer, ForeignKey('to.id')),
)

_EmailCc = Table(
    'emailcc',
    _Base.metadata,
    Column('email_id', Integer, ForeignKey('email.uid')),
    Column('cc_id', Integer, ForeignKey('cc.id')),
)

_EmailBcc = Table(
    'emailbcc',
    _Base.metadata,
    Column('email_id', Integer, ForeignKey('email.uid')),
    Column('bcc_id', Integer, ForeignKey('bcc.id')),
)

_EmailAttachment = Table(
    'emailattachment',
    _Base.metadata,
    Column('email_id', Integer, ForeignKey('email.uid')),
    Column('attachment_id', Integer, ForeignKey('attachment.uid')),
)


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

    uid = Column(String(length=64), primary_key=True)
    filename = Column(Text)
    content = Column(BLOB)
    cid = Column(Text)

    def to_dict(self):
        return {
            '_uid': self.uid,
            'filename': self.filename,
            'content': self.content,
            'cid': self.cid,
        }

    @classmethod
    def from_dict(cls, db, attachment):
        self = db.query(_Attachment).get(attachment.get('_uid'))
        if not self:
            self = _Attachment(
                uid=attachment.get('_uid'),
                filename=attachment.get('filename'),
                content=attachment.get('content'),
                cid=attachment.get('cid'),
            )

        for pointer in attachment.pop('emails', []):
            if isinstance(pointer, _Email):
                email = pointer
                add_to_session = False
            else:
                email = db.query(_Email).get(pointer)
                add_to_session = True

            if email:
                email.attachments.append(self)
                if add_to_session:
                    db.add(email)

        return self


class _Email(_Base):
    __tablename__ = 'email'

    uid = Column(String(length=64), primary_key=True)
    subject = Column(Text)
    body = Column(Text)
    sent_at = Column(DateTime())
    read = Column(Boolean, default=False, nullable=False)
    sender = Column(String(length=128), index=True)
    attachments = relationship(_Attachment, secondary=_EmailAttachment, backref='emails', lazy='joined')
    to = relationship(_To, secondary=_EmailTo, lazy='joined')
    cc = relationship(_Cc, secondary=_EmailCc, lazy='joined')
    bcc = relationship(_Bcc, secondary=_EmailBcc, lazy='joined')

    def to_dict(self):
        attachments = self.attachments
        attachments = ([attachment.to_dict() for attachment in attachments] if attachments else None)

        sent_at = self.sent_at
        sent_at = (sent_at.strftime('%Y-%m-%d %H:%M') if sent_at else None)

        return {
            k: v
            for (k, v) in (
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
            ) if v
        }

    @classmethod
    def from_dict(cls, db, email):
        sent_at = email.get('sent_at')
        sent_at = (datetime.strptime(sent_at, '%Y-%m-%d %H:%M') if sent_at else None)

        self = _Email(
            uid=email['_uid'],
            to=[get_or_create(db, _To, address=_.lower()) for _ in email.get('to', [])],
            cc=[get_or_create(db, _Cc, address=_.lower()) for _ in email.get('cc', [])],
            bcc=[get_or_create(db, _Bcc, address=_.lower()) for _ in email.get('bcc', [])],
            subject=email.get('subject'),
            body=email.get('body'),
            sent_at=sent_at,
            read=email.get('read', False),
            sender=email.get('from', '').lower() or None,
        )

        for attachment in email.get('attachments', []):
            attachment['emails'] = [self]
            db.add(_Attachment.from_dict(db, attachment))

        return self

    @classmethod
    def is_sent_by(cls, email_address):
        email_address = email_address.lower()
        return cls.sender == email_address

    @classmethod
    def is_received_by(cls, email_address):
        email_address = email_address.lower()
        to = cls.to.any(_To.address == email_address)
        cc = cls.cc.any(_Cc.address == email_address)
        bcc = cls.bcc.any(_Bcc.address == email_address)
        return to | cc | bcc


class _SqlalchemyEmailStore(EmailStore):
    def __init__(self, page_size: int, database_uri: str, restricted=None):
        super().__init__(restricted)
        self._page_size = page_size
        self._base = _Base
        self._engine = create_database(database_uri, self._base)
        self._sesion_maker = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)

    def _dbread(self):
        return session(self._sesion_maker, commit=False)

    def _dbwrite(self):
        return session(self._sesion_maker, commit=True)

    def _create(self, emails_or_attachments):
        last_type = ''

        with self._dbwrite() as db:
            for email_or_attachment in emails_or_attachments:
                type_ = email_or_attachment.get('_type', '')
                if type_ != last_type:
                    db.commit()
                    last_type = type_

                if not type_ or type_ == 'email':
                    self._create_email(db, email_or_attachment)
                elif type_ == 'attachment':
                    self._create_attachment(db, email_or_attachment)

    @classmethod
    def _create_email(cls, db, email):
        uid_exists = exists().where(_Email.uid == email['_uid'])
        if not db.query(uid_exists).scalar():
            db.add(_Email.from_dict(db, email))

    @classmethod
    def _create_attachment(cls, db, attachment):
        uid_exists = exists().where(_Attachment.uid == attachment['_uid'])
        if not db.query(uid_exists).scalar():
            db.add(_Attachment.from_dict(db, attachment))

    def _mark_sent(self, uids):
        now = datetime.utcnow()
        set_sent_at = {_Email.sent_at: now}

        with self._dbwrite() as db:
            db.query(_Email)\
                .filter(_match_email_uid(uids))\
                .update(set_sent_at, synchronize_session='fetch')

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

    def _find(self, query, table=_Email):
        with self._dbread() as db:
            results = db.query(table).filter(query)
            result = results.first()
        return result.to_dict() if result else None

    def _query(self, query, page):
        with self._dbread() as db:
            results = db.query(_Email).filter(query)
            results = results.order_by(_Email.sent_at.desc())

            if page is None:
                results = results.all()
                emails = (email.to_dict() for email in results)
            else:
                page = max(0, page - 1)
                results = results.offset(page * self._page_size).limit(self._page_size)
                emails = [email.to_dict() for email in results]

        return emails

    def inbox(self, email_address, page):
        return self._query(_Email.is_received_by(email_address), page)

    def outbox(self, email_address, page):
        return self._query(_Email.is_sent_by(email_address) & _Email.sent_at.is_(None), page)

    def search(self, email_address, page, query):
        textquery = '%{}%'.format(query)
        contains_query = or_(*(
            _Email.subject.ilike(textquery),
            _Email.body.ilike(textquery),
            _Email.sender.ilike(textquery),
            _Email.to.any(_To.address.ilike(textquery)),
            _Email.cc.any(_Cc.address.ilike(textquery)),
            _Email.bcc.any(_Bcc.address.ilike(textquery)),
        ))
        return self._query(_can_access(email_address) & contains_query, page)

    def pending(self, page):
        return self._query(_Email.sent_at.is_(None), page)

    def has_unread(self, email_address):
        with self._dbread() as db:
            unread = exists().where(_Email.read.is_(False) & _Email.is_received_by(email_address))
            has_unread_emails = db.query(unread).scalar()
        return has_unread_emails

    def num_pending(self):
        with self._dbread() as db:
            count = db.query(_Email)\
                .filter(_Email.sent_at.is_(None))\
                .count()
        return count

    def get(self, uid):
        return self._find(_Email.uid == uid)

    def get_attachment(self, email_id, attachment_id):
        return self._find(_Attachment.uid == attachment_id, table=_Attachment)

    def sent(self, email_address, page):
        return self._query(_Email.is_sent_by(email_address) & _Email.sent_at.isnot(None), page)


class SqliteEmailStore(_SqlalchemyEmailStore):
    def __init__(self, page_size: int, database_path: str, restricted=None):
        super().__init__(
            page_size=page_size,
            database_uri='sqlite:///{}'.format(database_path),
            restricted=restricted,
        )


def _can_access(email_address):
    return _Email.is_sent_by(email_address) | _Email.is_received_by(email_address)


def _match_email_uid(uids):
    return _Email.uid.in_(uids)
