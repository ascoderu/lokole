from flask_babel import gettext
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

from ascoderu_webapp.models import User


MESSAGES = {
    'email_field': gettext('Name or Email'),
    'email_field_required': gettext('Please enter your name or email.'),
    'name_field': gettext('Name'),
    'name_field_required': gettext('Please enter your name.'),
    'email_to_field': gettext('To'),
    'email_to_field_required': gettext('Please specify a recipient.'),
    'email_to_field_invalid': gettext('Must be a user name or email address.'),
    'email_subject_field': gettext('Subject'),
    'email_body_field': gettext('Message'),
    'email_submit_field': gettext('Send'),
}


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
        label=MESSAGES['email_field'],
        validators=[DataRequired(MESSAGES['email_field_required'])])


class RegisterForm(BaseRegisterForm):
    email = StringField(
        label=MESSAGES['name_field'],
        validators=[DataRequired(MESSAGES['name_field_required'])])


class NewEmailForm(Form):
    to = StringField(
        label=MESSAGES['email_to_field'],
        validators=[DataRequired(MESSAGES['email_to_field_required']),
                    EmailOrLocalUser(MESSAGES['email_to_field_invalid'])])

    subject = StringField(
        label=MESSAGES['email_subject_field'],
        validators=[Optional()])

    body = TextAreaField(
        label=MESSAGES['email_body_field'],
        validators=[Optional()])

    submit = SubmitField(
        label=MESSAGES['email_submit_field'])
