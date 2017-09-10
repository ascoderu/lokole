from typing import Iterable
from typing import List
from typing import Optional

from flask import render_template
from flask import request
from flask_login import current_user
from flask_wtf import Form
from werkzeug.datastructures import FileStorage
from wtforms import FileField
from wtforms import StringField
from wtforms import SubmitField
from wtforms.validators import DataRequired
from wtforms.validators import Optional as DataOptional

from opwen_email_client.domain.email.attachment import AttachmentEncoder
from opwen_email_client.domain.email.store import EmailStore
from opwen_email_client.util.wtforms import Emails
from opwen_email_client.util.wtforms import HtmlTextAreaField
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.config import i8n


class NewEmailForm(Form):
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

    def as_dict(self, attachment_encoder: AttachmentEncoder) -> dict:
        attachments = request.files.getlist(self.attachments.name)
        form = {key: value for (key, value) in self.data.items() if value}
        form.pop('submit', None)
        form['sent_at'] = None
        form['read'] = True
        form['from'] = current_user.email
        form['to'] = _split_emails(form.get('to'))
        form['cc'] = _split_emails(form.get('cc'))
        form['bcc'] = _split_emails(form.get('bcc'))
        form['body'] = form.get('body')
        form['attachments'] = list(_attachments_as_dict(attachments,
                                                        attachment_encoder))
        return form

    def _populate(self, email: dict):
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

        uid = request.args.get('uid')
        if uid:
            reference = email_store.get(uid)
            if not reference or not current_user.can_access(reference):
                return None
            form._populate(reference)

        return form


class ReplyEmailForm(NewEmailForm):
    action_name = 'reply'

    def _populate(self, email: dict):
        self.to.data = email.get('from', '')
        self.subject.data = 'Re: {}'.format(email.get('subject', ''))
        self.body.data = render_template('emails/reply.html', email=email)


class ReplyAllEmailForm(NewEmailForm):
    action_name = 'reply_all'

    def _populate(self, email: dict):
        self.to.data = _join_emails(email.get('from'), *email.get('cc', []))
        self.subject.data = 'Re: {}'.format(email.get('subject', ''))
        self.body.data = render_template('emails/reply.html', email=email)


class ForwardEmailForm(NewEmailForm):
    action_name = 'forward'

    def _populate(self, email: dict):
        self.subject.data = 'Fwd: {}'.format(email.get('subject', ''))
        self.body.data = render_template('emails/forward.html', email=email)


def _attachments_as_dict(
        filestorages: Iterable[FileStorage],
        attachment_encoder: AttachmentEncoder) -> Iterable[dict]:

    for filestorage in filestorages:
        filename = filestorage.filename
        content = attachment_encoder.encode(filestorage.stream.read())
        if filename and content:
            yield {'filename': filename, 'content': content}


def _join_emails(*emails: str) -> str:
    delimiter = '{0} '.format(AppConfig.EMAIL_ADDRESS_DELIMITER)
    return delimiter.join(email for email in emails if email)


def _split_emails(emails: Optional[str]) -> List[str]:
    if not emails:
        return []

    addresses = emails.split(AppConfig.EMAIL_ADDRESS_DELIMITER)
    return [address.strip() for address in addresses]
