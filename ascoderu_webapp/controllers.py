from datetime import datetime

from ascoderu_webapp import db
from ascoderu_webapp.models import Email
from ascoderu_webapp.models import User
from utils.strings import istreq


def _query_emails_by(user):
    def query_user_email():
        return Email.sender.ilike(user.email)

    def query_user_name():
        return Email.sender.ilike(user.name)

    if user.email and user.name:
        return query_user_email() | query_user_name()
    elif user.email:
        return query_user_email()
    elif user.name:
        return query_user_name()
    raise ValueError('one of user.email or user.name must be set')


def _query_user(name_or_email):
    return User.query.filter(User.name.ilike(name_or_email) |
                             User.email.ilike(name_or_email)).first()


def user_exists(name_or_email):
    if not name_or_email:
        return False

    user = _query_user(name_or_email)
    return user is not None


def outbox_emails_for(user):
    query = Email.date.is_(None) & _query_emails_by(user)
    return Email.query.filter(query).all()


def sent_emails_for(user):
    query = Email.date.isnot(None) & _query_emails_by(user)
    return Email.query.filter(query).all()


def inbox_emails_for(user):
    return [mail for mail in Email.query.all()
            if any(istreq(to, user.email) or istreq(to, user.name)
                   for to in mail.to)]


def new_email_for(user, to, subject, body):
    is_to_local_user = user_exists(to)
    email_date = datetime.now() if is_to_local_user else None

    db.session.add(Email(
        date=email_date,
        to=[to],
        sender=user.email or user.name,
        subject=subject,
        body=body))
    db.session.commit()

    return is_to_local_user
