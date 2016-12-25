from flask import render_template
from flask import request
from flask_login import current_user
from flask_wtf import Form

from opwen_infrastructure.wtforms import EmailField
from opwen_infrastructure.wtforms import HtmlTextAreaField
from wtforms import FileField
from wtforms import StringField
from wtforms import SubmitField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.validators import Optional

from opwen_email_client.config import i8n


class NewEmailForm(Form):
    to = EmailField(
        validators=[DataRequired(i8n.EMAIL_TO_REQUIRED),
                    Email(i8n.EMAIL_ADDRESS_INVALID)])

    cc = EmailField(
        validators=[Optional(),
                    Email(i8n.EMAIL_ADDRESS_INVALID)])

    bcc = EmailField(
        validators=[Optional(),
                    Email(i8n.EMAIL_ADDRESS_INVALID)])

    subject = StringField(
        validators=[Optional()])

    body = HtmlTextAreaField(
        validators=[Optional()])

    attachments = FileField(
        validators=[Optional()],
        render_kw={'multiple': True})

    submit = SubmitField()

    def _handle_reply(self, email):
        """
        :type email: dict

        """
        self.to.data = email.get('from', '')
        self.subject.data = 'Re: {}'.format(email.get('subject', ''))

    def _handle_reply_all(self, email):
        """
        :type email: dict

        """
        self.to.data = self._join_emails(email.get('from'), *email.get('cc', []))
        self.subject.data = 'Re: {}'.format(email.get('subject', ''))

    def _handle_forward(self, email):
        """
        :type email: dict

        """
        self.subject.data = 'Fwd: {}'.format(email.get('subject', ''))
        self.body.data = render_template('_forwarded.html', email=email)

    def handle_action(self, email_store):
        """
        :type email_store: opwen_domain.email.EmailStore

        """
        uid = request.args.get('uid')
        action = request.args.get('action')
        if not uid or not action:
            return

        reference = email_store.get(uid)
        if not reference or not current_user.can_access(reference):
            return

        if action == 'reply':
            self._handle_reply(reference)
        elif action == 'reply_all':
            self._handle_reply_all(reference)
        elif action == 'forward':
            self._handle_forward(reference)

    def as_dict(self, attachment_encoder):
        """
        :type attachment_encoder: opwen_domain.email.interfaces.AttachmentEncoder
        :rtype: dict

        """
        attachments = request.files.getlist(self.attachments.name)
        form = {key: value for (key, value) in self.data.items() if value}
        form.pop('submit', None)
        form['sent_at'] = None
        form['from'] = current_user.email
        form['to'] = self._split_emails(form.get('to'))
        form['cc'] = self._split_emails(form.get('cc'))
        form['bcc'] = self._split_emails(form.get('bcc'))
        form['body'] = form.get('body')
        form['attachments'] = list(self._attachments_as_dict(attachments, attachment_encoder))
        return form

    @classmethod
    def _join_emails(cls, *emails):
        """
        :type emails: list[str]
        :rtype: str

        """
        return ', '.join(filter(None, emails))

    @classmethod
    def _split_emails(cls, emails):
        """
        :type emails: str | None
        :rtype: list[str]

        """
        return list(map(str.strip, emails.split(','))) if emails else []

    @classmethod
    def _attachments_as_dict(cls, filestorages, attachment_encoder):
        """
        :type filestorages: collections.Iterable[werkzeug.datastructures.FileStorage]
        :type attachment_encoder: opwen_domain.email.interfaces.AttachmentEncoder
        :rtype: collections.Iterable[dict]

        """
        for filestorage in filestorages:
            filename = filestorage.filename
            content = attachment_encoder.encode(filestorage.stream.read())
            if filename and content:
                yield {'filename': filename,
                       'content': content}

    @classmethod
    def from_request(cls, email_store):
        """
        :type email_store: opwen_domain.email.EmailStore
        :rtype: opwen_web.forms.NewEmailForm

        """
        form = cls(request.form)
        form.handle_action(email_store)
        return form
