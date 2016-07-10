from datetime import datetime

from ascoderu_webapp import db
from ascoderu_webapp.models import Email
from ascoderu_webapp.models import User


def outbox_emails_for(user):
    return Email.query.filter(Email.date.is_(None) &
                              (Email.sender.is_(user.email) |
                               Email.sender.is_(user.name)))


def sent_emails_for(user):
    return Email.query.filter(Email.date.isnot(None) &
                              (Email.sender.is_(user.email) |
                               Email.sender.is_(user.name)))


def inbox_emails_for(user):
    return [mail for mail in Email.query.all()
            if any(to == user.email or to == user.name for to in mail.to)]


def new_email_for(user, to, subject, body):
    is_to_local_user = User.exists(to)
    email_date = datetime.now() if is_to_local_user else None

    db.session.add(Email(
        date=email_date,
        to=[to],
        sender=user.email or user.name,
        subject=subject,
        body=body))
    db.session.commit()

    return is_to_local_user
