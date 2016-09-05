from flask_babel import lazy_gettext as _
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
from wtforms.widgets import Input

from opwen_webapp.controllers import user_exists


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


class EmailInput(Input):
    input_type = 'email'


class EmailField(StringField):
    widget = EmailInput()


class LoginForm(BaseLoginForm):
    email = StringField(
        label=_('Name or Email'),
        validators=[DataRequired(_('Please enter your name or email.'))])

    password = PasswordField(_('Password'))

    submit = SubmitField(_('Login'))


class RegisterForm(BaseRegisterForm):
    email = StringField(
        label=_('Name'),
        validators=[DataRequired(_('Please enter your name.')),
                    UserDoesNotAlreadyExist(_('Sorry, this name is already in use.'))])

    password = PasswordField(
        label=_('Password'),
        validators=[DataRequired(_('Please provide a password')),
                    Length(6, 128, _('Password must be at least 6 characters'))])

    password_confirm = PasswordField(
        label=_('Retype password'),
        validators=[EqualTo('password', _('Password does not match'))])

    submit = SubmitField(_('Register'))


class NewEmailForm(Form):
    to = EmailField(
        label=_('To'),
        validators=[DataRequired(_('Please specify a recipient.')),
                    EmailOrLocalUser(_('Must be a user name or email address.'))])

    subject = StringField(
        label=_('Subject'),
        validators=[Optional()])

    body = TextAreaField(
        label=_('Message'),
        validators=[Optional()])

    attachments = FileField(
        label=_('Attachments'),
        validators=[Optional()],
        render_kw={'multiple': True})

    submit = SubmitField(
        label=_('Send'))
