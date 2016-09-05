from datetime import datetime

from flask import render_template
from flask_babel import gettext as _
from werkzeug.utils import secure_filename

from opwen_webapp import app
from opwen_webapp import db
from opwen_webapp import uploads
from opwen_webapp.models import Addressee
from opwen_webapp.models import Attachment
from opwen_webapp.models import Email
from opwen_webapp.models import SyncReport
from opwen_webapp.models import User
from utils.networking import use_interface
from utils.strings import normalize_caseless
from utils.temporary import removing


def _find_emails_by(user):
    """
    :type user: User
    :rtype: flask_sqlalchemy.BaseQuery
    :raises ValueError: if the user instance is invalid

    """
    def query_user_email():
        return Email.sender.is_(user.email)

    def query_user_name():
        return Email.sender.is_(user.name)

    if user.email and user.name:
        return query_user_email() | query_user_name()
    raise ValueError('one of user.email or user.name must be set')


def _find_user_by(name_or_email):
    """
    :type name_or_email: str
    :rtype: User | None

    """
    if not name_or_email:
        return None

    name_or_email = normalize_caseless(name_or_email)
    return User.query.filter(User.name.is_(name_or_email) |
                             User.email.is_(name_or_email)).first()


def user_exists(name_or_email):
    """
    :type name_or_email: str

    """
    user = _find_user_by(name_or_email)
    return user is not None


def outbox_emails_for(user):
    """
    :type user: User
    :rtype: flask_sqlalchemy.BaseQuery

    """
    query = Email.date.is_(None) & _find_emails_by(user)
    return Email.query.filter(query)


def sent_emails_for(user):
    """
    :type user: User
    :rtype: flask_sqlalchemy.BaseQuery

    """
    query = Email.date.isnot(None) & _find_emails_by(user)
    return Email.query.filter(query)


def inbox_emails_for(user):
    """
    :type user: User
    :rtype: flask_sqlalchemy.BaseQuery

    """
    is_to_user = Addressee.val.is_(user.email) | Addressee.val.is_(user.name)
    return Email.query.join(Email.to_relationship).filter(is_to_user)


def new_email_for(user, to, subject, body, attachments=()):
    """
    :type user: User
    :type to: str
    :type subject: str
    :type body: str
    :type attachments: list[werkzeug.datastructures.FileStorage]

    """
    is_to_local_user = user_exists(to)
    email_date = datetime.utcnow() if is_to_local_user else None
    attachments = [(uploads.save(attachment), attachment.filename)
                   for attachment in attachments
                   if attachment and attachment.filename]

    db.session.add(Email(
        date=email_date,
        to=[to],
        sender=user.email or user.name,
        subject=subject,
        body=body,
        attachments=attachments,
    ))
    db.session.commit()

    return is_to_local_user


def find_attachment(user, filename):
    """
    :type user: User
    :type filename: str
    :rtype: Attachment | None

    """
    attached_name = normalize_caseless(secure_filename(filename))
    email = (inbox_emails_for(user)
             .join(Email.attachments)
             .filter(Attachment.name == attached_name)
             .first())

    if not email:
        return None

    return next(attachment for attachment in email.attachments
                if attachment.name == attached_name)  # pragma: no branch


def upload_local_updates():
    """
    :rtype: int

    """
    emails = Email.query.filter(Email.date.is_(None)).all()
    now = datetime.utcnow()
    for email in emails:
        email.date = now

    with removing(app.serializer.serialize(emails)) as serialized:
        app.remote_storage.upload(serialized)
    db.session.commit()

    return len(emails)


def download_remote_updates():
    """
    :rtype: int

    """
    with removing(app.remote_storage.download()) as downloaded:
        emails, accounts = app.serializer.deserialize(downloaded)

    for email in emails:
        if email.is_complete():
            for attachment in email.attachments:
                attachment.path = uploads.save(attachment.path)
            db.session.add(email)
    for account in accounts:
        user = _find_user_by(account.name)
        if user and account.name and account.email:
            user.name = account.name
            user.email = account.email
            send_account_finalized_email(user)
            db.session.add(user)
    db.session.commit()

    return len(emails)


def sync_with_remote(internet_interface_name):
    """
    :type internet_interface_name: str
    :rtype: SyncReport

    """
    with use_interface(internet_interface_name):
        number_of_emails_uploaded = upload_local_updates()
        number_of_emails_downloaded = download_remote_updates()

    return SyncReport(emails_uploaded=number_of_emails_uploaded,
                      emails_downloaded=number_of_emails_downloaded)


def send_welcome_email(user):
    """
    :type user: User

    """
    welcome_email = Email(
        date=datetime.utcnow(),
        to=[user.name],
        sender=_('Lokole team'),
        subject=_('Welcome!'),
        body=render_template('emails/account_created.html', name=user.name))

    db.session.add(welcome_email)
    db.session.commit()


def send_account_finalized_email(user):
    """
    :type user: User

    """
    account_created_email = Email(
        date=datetime.utcnow(),
        to=[user.name],
        sender=_('Lokole team'),
        subject=_('Your account is now fully set up.'),
        body=render_template('emails/account_finalized.html',
                             name=user.name, email=user.email))

    db.session.add(account_created_email)
    db.session.commit()
