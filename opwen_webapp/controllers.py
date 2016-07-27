from datetime import datetime

from werkzeug.utils import secure_filename

from opwen_webapp import app
from opwen_webapp import db
from opwen_webapp import uploads
from opwen_webapp.models import Email
from opwen_webapp.models import User
from utils.strings import normalize_caseless


def _find_emails_by(user):
    """
    :type user: User

    """
    def query_user_email():
        return Email.sender.is_(user.email)

    def query_user_name():
        return Email.sender.is_(user.name)

    if user.email and user.name:
        return query_user_email() | query_user_name()
    elif user.email:
        return query_user_email()
    elif user.name:
        return query_user_name()
    raise ValueError('one of user.email or user.name must be set')


def _find_user_by(name_or_email):
    """
    :type name_or_email: str

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
    :rtype: collections.Iterable[Email]

    """
    query = Email.date.is_(None) & _find_emails_by(user)
    return Email.query.filter(query)


def sent_emails_for(user):
    """
    :type user: User
    :rtype: collections.Iterable[Email]

    """
    query = Email.date.isnot(None) & _find_emails_by(user)
    return Email.query.filter(query)


def inbox_emails_for(user):
    """
    :type user: User
    :rtype: collections.Iterable[Email]

    """
    return [mail for mail in Email.query.all()
            if any(to == user.email or to == user.name
                   for to in mail.to)]


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
    attachments = [uploads.save(attachment) for attachment in attachments]

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
    :rtype: str | None

    """
    attached_name = normalize_caseless(secure_filename(filename))
    return next((uploads.path(filename)
                 for email in inbox_emails_for(user)
                 for attached in email.attachments or []
                 if attached == attached_name), None)


def upload_local_updates():
    emails = Email.query.filter(Email.date.is_(None)).all()
    now = datetime.utcnow()
    for email in emails:
        email.date = now

    packed = app.remote_packer.pack(emails)
    serialized = app.remote_serializer.serialize(packed)
    app.remote_storage.upload(serialized)
    db.session.commit()

    return len(emails)


def download_remote_updates():
    serialized = app.remote_storage.download()
    packed = app.remote_serializer.deserialize(serialized)
    emails = app.remote_packer.unpack_emails(packed)
    accounts = app.remote_packer.unpack_accounts(packed)

    for email in emails:
        if email.is_complete():
            db.session.add(email)
    for name, email in accounts:
        user = _find_user_by(name)
        if user and name and email:
            user.name = name
            user.email = email
            db.session.add(user)
    db.session.commit()

    return len(emails)
