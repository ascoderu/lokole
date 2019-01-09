from datetime import datetime
from itertools import chain
from typing import Iterable
from typing import List
from typing import Optional

from flask import render_template
from flask import request
from flask_login import current_user
from flask_wtf import FlaskForm
from werkzeug.datastructures import FileStorage
from wtforms import FileField
from wtforms import StringField
from wtforms import SubmitField
from wtforms.validators import DataRequired
from wtforms.validators import Optional as DataOptional

from opwen_email_client.domain.email.store import EmailStore
from opwen_email_client.util.wtforms import Emails
from opwen_email_client.util.wtforms import HtmlTextAreaField
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.config import i8n


class NewEmailForm(FlaskForm):
    to = StringField(
        validators=[DataRequired(i8n.EMAIL_TO_REQUIRED),
                    Emails(AppConfig.EMAIL_ADDRESS_DELIMITER,
                           i8n.EMAIL_ADDRESS_INVALID)])

    cc = StringField(
        validators=[DataOptional(),
                    Emails(AppConfig.EMAIL_ADDRESS_DELIMITER,
                           i8n.EMAIL_ADDRESS_INVALID)])

    bcc = StringField(
        validators=[DataOptional(),
                    Emails(AppConfig.EMAIL_ADDRESS_DELIMITER,
                           i8n.EMAIL_ADDRESS_INVALID)])

    subject = StringField(
        validators=[DataOptional()])

    body = HtmlTextAreaField(
        validators=[DataOptional()])

    attachments = FileField(
        validators=[DataOptional()],
        render_kw={'multiple': True})

    submit = SubmitField()

    def as_dict(self) -> dict:
        form = {key: value for (key, value) in self.data.items() if value}
        form.pop('submit', None)

        attachments = request.files.getlist(self.attachments.name)
        to = _split_emails(form.get('to'))
        cc = _split_emails(form.get('cc'))
        bcc = _split_emails(form.get('bcc'))

        sent_at = None
        if all(_is_local_message(address) for address in chain(to, cc, bcc)):
            sent_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M')

        form['sent_at'] = sent_at
        form['read'] = True
        form['from'] = current_user.email
        form['to'] = to
        form['cc'] = cc
        form['bcc'] = bcc
        form['body'] = form.get('body')
        form['subject'] = form.get('subject', i8n.EMAIL_NO_SUBJECT)
        form['attachments'] = list(_attachments_as_dict(attachments))
        return form

    def _populate(self, email: Optional[dict], to: Optional[str]):
        pass

    @classmethod
    def _new_instance_for(cls, action_name: Optional[str]):
        if not action_name:
            return cls(request.form)

        try:
            clazz = next(clazz for clazz in NewEmailForm.__subclasses__()
                         if getattr(clazz, 'action_name', None) == action_name)
        except StopIteration:
            return None
        else:
            return clazz(request.form)

    @classmethod
    def from_request(cls, email_store: EmailStore):
        action_name = request.args.get('action')
        form = cls._new_instance_for(action_name)
        if not form:
            return None

        to = request.args.get('to')
        uid = request.args.get('uid')
        reference = None
        if uid:
            reference = email_store.get(uid)
            if not current_user.can_access(reference):
                reference = None
        form._populate(reference, to)

        return form


class ToEmailForm(NewEmailForm):
    action_name = 'to'

    # noinspection PyUnusedLocal
    def _populate(self, email: Optional[dict], to: Optional[str]):
        self.to.data = to or ''


class ReplyEmailForm(NewEmailForm):
    action_name = 'reply'

    # noinspection PyUnusedLocal
    def _populate(self, email: Optional[dict], to: Optional[str]):
        if not email:
            return

        self.to.data = email.get('from', '')
        self.subject.data = 'Re: {}'.format(email.get('subject', ''))
        self.body.data = render_template('emails/reply.html', email=email)


class ReplyAllEmailForm(NewEmailForm):
    action_name = 'reply_all'

    # noinspection PyUnusedLocal
    def _populate(self, email: Optional[dict], to: Optional[str]):
        if not email:
            return

        self.to.data = _join_emails(email.get('from'), *email.get('cc', []))
        self.subject.data = 'Re: {}'.format(email.get('subject', ''))
        self.body.data = render_template('emails/reply.html', email=email)


class ForwardEmailForm(NewEmailForm):
    action_name = 'forward'

    # noinspection PyUnusedLocal
    def _populate(self, email: Optional[dict], to: Optional[str]):
        if not email:
            return

        self.subject.data = 'Fwd: {}'.format(email.get('subject', ''))
        self.body.data = render_template('emails/forward.html', email=email)


def _attachments_as_dict(filestorages: Iterable[FileStorage]) \
        -> Iterable[dict]:

    for filestorage in filestorages:
        filename = filestorage.filename
        content = filestorage.stream.read()
        if filename and content:
            yield {'filename': filename, 'content': content}


def _is_local_message(address: str) -> bool:
    host = address.split('@')[-1]
    return host.lower() == AppConfig.CLIENT_EMAIL_HOST.lower()


def _join_emails(*emails: str) -> str:
    delimiter = '{0} '.format(AppConfig.EMAIL_ADDRESS_DELIMITER)
    return delimiter.join(email for email in emails if email)


def _split_emails(emails: Optional[str]) -> List[str]:
    if not emails:
        return []

    addresses = emails.split(AppConfig.EMAIL_ADDRESS_DELIMITER)
    return [address.strip() for address in addresses]
