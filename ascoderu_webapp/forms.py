from flask_security import LoginForm as BaseLoginForm
from flask_security import RegisterForm as BaseRegisterForm
from flask_wtf import Form
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TextAreaField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.validators import Optional
from wtforms.validators import ValidationError

from ascoderu_webapp.controllers import user_exists
from config import ui


class UserDoesNotAlreadyExist(object):
    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        if user_exists(field.data):
            raise ValidationError(self.message)


class EmailOrLocalUser(object):
    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        try:
            Email(self.message)(form, field)
        except ValidationError:
            if not user_exists(field.data):
                raise


class LoginForm(BaseLoginForm):
    email = StringField(
        label=ui('email_field'),
        validators=[DataRequired(ui('email_field_required'))])


class RegisterForm(BaseRegisterForm):
    email = StringField(
        label=ui('name_field'),
        validators=[DataRequired(ui('name_field_required')),
                    UserDoesNotAlreadyExist(ui('name_field_already_exists'))])


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

    submit = SubmitField(
        label=ui('email_submit_field'))
