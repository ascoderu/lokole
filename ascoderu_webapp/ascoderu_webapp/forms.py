from flask_babel import gettext
from flask_security import LoginForm as BaseLoginForm
from flask_security import RegisterForm as BaseRegisterForm
from wtforms import StringField
from wtforms.validators import DataRequired


MESSAGES = {
    'email_field': gettext('Name or Email'),
    'email_field_required': gettext('Please enter your name or email.'),
    'name_field': gettext('Name'),
    'name_field_required': gettext('Please enter your name.'),
}


class LoginForm(BaseLoginForm):
    email = StringField(
        label=MESSAGES['email_field'],
        validators=[DataRequired(MESSAGES['email_field_required'])])


class RegisterForm(BaseRegisterForm):
    email = StringField(
        label=MESSAGES['name_field'],
        validators=[DataRequired(MESSAGES['name_field_required'])])
