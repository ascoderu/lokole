from datetime import datetime
from io import BytesIO
from itertools import chain
from mimetypes import guess_type
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple

from flask import render_template
from flask import request
from flask_login import current_user
from flask_wtf import FlaskForm
from PIL import Image
from werkzeug.datastructures import FileStorage
from wtforms import FileField
from wtforms import SelectMultipleField
from wtforms import StringField
from wtforms import SubmitField
from wtforms.validators import DataRequired
from wtforms.validators import Optional as DataOptional

from opwen_email_client.domain.email.store import EmailStore
from opwen_email_client.util.wtforms import Emails
from opwen_email_client.util.wtforms import HtmlTextAreaField
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.config import ImageDimensions
from opwen_email_client.webapp.config import i8n


class NewEmailForm(FlaskForm):
    to = StringField(validators=[
        DataRequired(i8n.EMAIL_TO_REQUIRED),
        Emails(AppConfig.EMAIL_ADDRESS_DELIMITER, i8n.EMAIL_ADDRESS_INVALID),
    ])

    cc = StringField(validators=[
        DataOptional(),
        Emails(AppConfig.EMAIL_ADDRESS_DELIMITER, i8n.EMAIL_ADDRESS_INVALID),
    ])

    bcc = StringField(validators=[
        DataOptional(),
        Emails(AppConfig.EMAIL_ADDRESS_DELIMITER, i8n.EMAIL_ADDRESS_INVALID),
    ])

    subject = StringField(validators=[DataOptional()])

    body = HtmlTextAreaField(validators=[
        DataOptional(),
    ])

    forwarded_attachments = SelectMultipleField(choices=[], validators=[
        DataOptional(),
    ])

    attachments = FileField(validators=[
        DataOptional(),
    ], render_kw={
        'multiple': True,
    })

    submit = SubmitField()

    def as_dict(self, email_store: EmailStore) -> dict:
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

    def _populate(self, email_store: EmailStore):
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

    def _get_reference_email(self, email_store: EmailStore) -> Optional[dict]:
        uid = request.args.get('uid', '')
        if not uid:
            return None

        reference = email_store.get(uid)
        if not self._can_access(current_user, reference):
            return None

        return reference

    @classmethod
    def _can_access(cls, user, email: dict) -> bool:
        actors = set()
        actors.add(email.get('from'))
        actors.update(email.get('to', []))
        actors.update(email.get('cc', []))
        actors.update(email.get('bcc', []))

        return user.email in actors

    @classmethod
    def from_request(cls, email_store: EmailStore):
        action_name = request.args.get('action')
        form = cls._new_instance_for(action_name)
        if not form:
            return None

        form._populate(email_store)

        return form


class ToEmailForm(NewEmailForm):
    action_name = 'to'

    # noinspection PyUnusedLocal
    def _populate(self, email_store: EmailStore):
        if not self.to.data:
            self.to.data = request.args.get('to', '')


class ReplyEmailForm(NewEmailForm):
    action_name = 'reply'

    def _populate(self, email_store: EmailStore):
        email = self._get_reference_email(email_store)
        if not email:
            return

        if not self.to.data:
            self.to.data = email.get('from', '')

        if not self.subject.data:
            self.subject.data = 'Re: {}'.format(email.get('subject', ''))

        if not self.body.data:
            self.body.data = render_template('emails/reply.html', email=email)


class ReplyAllEmailForm(NewEmailForm):
    action_name = 'reply_all'

    def _populate(self, email_store: EmailStore):
        email = self._get_reference_email(email_store)
        if not email:
            return

        if not self.to.data:
            self.to.data = _join_emails(email.get('from'), *email.get('cc', []))

        if not self.subject.data:
            self.subject.data = 'Re: {}'.format(email.get('subject', ''))

        if not self.body.data:
            self.body.data = render_template('emails/reply.html', email=email)


class ForwardEmailForm(NewEmailForm):
    action_name = 'forward'

    def _populate(self, email_store: EmailStore):
        email = self._get_reference_email(email_store)
        if not email:
            return

        if not self.subject.data:
            self.subject.data = 'Fwd: {}'.format(email.get('subject', ''))

        if not self.body.data:
            self.body.data = render_template('emails/forward.html', email=email)

        self._set_forwarded_attachments(email)

    def _set_forwarded_attachments(self, email):
        attachment_filenames = [attachment.get('filename') for attachment in email.get('attachments', [])]

        self.forwarded_attachments.choices = [(filename, filename) for filename in attachment_filenames]

        self.forwarded_attachments.render_kw = {
            'size': len(attachment_filenames),
        }

        if not self.forwarded_attachments.data:
            self.forwarded_attachments.data = [filename for filename in attachment_filenames]

    def as_dict(self, email_store: EmailStore):
        form = super().as_dict(email_store)
        new_attachments = form.get('attachments', [])

        reference_email = self._get_reference_email(email_store)

        forwarded_attachments = [
            attachment for attachment in reference_email.get('attachments', [])
            if attachment.get('filename') in self.forwarded_attachments.data
        ]

        form['attachments'] = forwarded_attachments + new_attachments

        return form


def _attachments_as_dict(filestorages: Iterable[FileStorage]) \
        -> Iterable[dict]:

    for filestorage in filestorages:
        filename = filestorage.filename
        content = filestorage.stream.read()

        formatted_content = _format_attachment(filename, content)

        if filename and formatted_content:
            yield {'filename': filename, 'content': formatted_content}


def _format_attachment(filename: str, content: bytes) -> bytes:
    attachment_type = guess_type(filename)[0]

    if not attachment_type:
        return content

    if 'image' in attachment_type.lower():
        content = _change_image_size(content)

    return content


def _is_already_small(size: Tuple[int, int]) -> bool:
    width, height = size
    return width <= ImageDimensions.MAX_WIDTH_IMAGES and height <= ImageDimensions.MAX_HEIGHT_IMAGES


def _change_image_size(image_content_bytes: bytes) -> bytes:
    image_bytes = BytesIO(image_content_bytes)
    image_bytes.seek(0)
    image = Image.open(image_bytes)

    if _is_already_small(image.size):
        return image_content_bytes

    new_size = (ImageDimensions.MAX_WIDTH_IMAGES, ImageDimensions.MAX_HEIGHT_IMAGES)
    image.thumbnail(new_size, Image.ANTIALIAS)
    new_image = BytesIO()
    image.save(new_image, image.format)
    new_image.seek(0)
    new_image_bytes = new_image.read()
    return new_image_bytes


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
