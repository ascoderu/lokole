from flask import request
from flask_login import current_user
from flask_wtf import Form
from wtforms import FileField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TextAreaField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.validators import Optional

from ca.ascoderu.lokole.infrastructure.wtforms import EmailField
from ca.ascoderu.lokole.web.config import i8n


class NewEmailForm(Form):
    to = EmailField(
        validators=[DataRequired(i8n.EMAIL_TO_REQUIRED),
                    Email(i8n.EMAIL_ADDRESS_INVALID)])

    subject = StringField(
        validators=[Optional()])

    body = TextAreaField(
        validators=[Optional()])

    attachments = FileField(
        validators=[Optional()],
        render_kw={'multiple': True})

    submit = SubmitField()

    def _set_fields_from_request(self, *fields):
        """
        :type fields: list[str]

        """
        for field in fields:
            value = request.args.get(field)
            if value:
                getattr(self, field).data = value

    def as_dict(self, attachment_encoder):
        """
        :type attachment_encoder: ca.ascoderu.lokole.domain.email.interfaces.AttachmentEncoder
        :rtype: dict

        """
        attachments = request.files.getlist(self.attachments.name)
        form = {key: value for (key, value) in self.data.items() if value}
        form.pop('submit', None)
        form['sent_at'] = None
        form['from'] = current_user.email
        form['to'] = self._split_emails(form.get('to'))
        form['attachments'] = list(self._attachments_as_dict(attachments, attachment_encoder))
        return form

    @classmethod
    def _split_emails(cls, emails):
        """
        :type emails: str | None
        :rtype: list[str]

        """
        return list(map(str.strip, emails.split(';'))) if emails else []

    @classmethod
    def _attachments_as_dict(cls, filestorages, attachment_encoder):
        """
        :type filestorages: collections.Iterable[werkzeug.datastructures.FileStorage]
        :type attachment_encoder: ca.ascoderu.lokole.domain.email.interfaces.AttachmentEncoder
        :rtype: collections.Iterable[dict]

        """
        for filestorage in filestorages:
            filename = filestorage.filename
            content = attachment_encoder.encode(filestorage.stream.read())
            yield {'filename': filename,
                   'content': content}

    @classmethod
    def from_request(cls):
        """
        :rtype: ca.ascoderu.lokole.web.forms.NewEmailForm

        """
        form = cls(request.form)
        form._set_fields_from_request('to', 'subject')
        return form
