from flask_security import LoginForm as BaseLoginForm
from flask_security import RegisterForm as BaseRegisterForm
from flask_wtf import Form
from wtforms import FileField
from wtforms import PasswordField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TextAreaField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.validators import EqualTo
from wtforms.validators import Length
from wtforms.validators import Optional
from wtforms.validators import ValidationError

from opwen_webapp.controllers import user_exists
from config import ui


class UserDoesNotAlreadyExist(object):
    def __init__(self, message=None):
        """
        :type message: str

        """
        self.message = message

    # noinspection PyUnusedLocal
    def __call__(self, form, field):
        """
        :type field: wtforms.Field

        """
        if user_exists(field.data):
            raise ValidationError(self.message)


class EmailOrLocalUser(object):
    def __init__(self, message=None):
        """
        :type message: str

        """
        self.message = message

    def __call__(self, form, field):
        """
        :type field: wtforms.Field

        """
        try:
            Email(self.message)(form, field)
        except ValidationError:
            if not user_exists(field.data):
                raise


class LoginForm(BaseLoginForm):
    email = StringField(
        label=ui('email_field'),
        validators=[DataRequired(ui('email_field_required'))])

    password = PasswordField(ui('password_field'))

    submit = SubmitField(ui('login'))


class RegisterForm(BaseRegisterForm):
    email = StringField(
        label=ui('name_field'),
        validators=[DataRequired(ui('name_field_required')),
                    UserDoesNotAlreadyExist(ui('name_field_already_exists'))])

    password = PasswordField(
        label=ui('password_field'),
        validators=[DataRequired(ui('password_field_required')),
                    Length(6, 128, ui('password_field_too_short'))])

    password_confirm = PasswordField(
        label=ui('password_confirm_field'),
        validators=[EqualTo('password', ui('password_field_must_match'))])

    submit = SubmitField(ui('register'))


class NewEmailForm(Form):
    to = StringField(
        label=ui('email_to_field'),
        validators=[DataRequired(ui('email_to_field_required')),
                    EmailOrLocalUser(ui('email_to_field_invalid'))])

    subject = StringField(
        label=ui('email_subject_field'),
        validators=[Optional()])

    body = TextAreaField(
        label=ui('email_body_field'),
        validators=[Optional()])

    attachments = FileField(
        label=ui('email_attachments_field'),
        validators=[Optional()],
        render_kw={'multiple': True})

    submit = SubmitField(
        label=ui('email_submit_field'))
