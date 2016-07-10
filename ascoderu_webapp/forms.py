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

from config import ui
from ascoderu_webapp.models import User


class EmailOrLocalUser(object):
    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        try:
            Email(self.message)(form, field)
        except ValidationError:
            if not User.exists(field.data):
                raise


class LoginForm(BaseLoginForm):
    email = StringField(
        label=ui('email_field'),
        validators=[DataRequired(ui('email_field_required'))])


class RegisterForm(BaseRegisterForm):
    email = StringField(
        label=ui('name_field'),
        validators=[DataRequired(ui('name_field_required'))])


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
