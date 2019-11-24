from flask_security import LoginForm as _LoginForm
from flask_security import RegisterForm as _RegisterForm
from flask_security.forms import email_required
from flask_security.forms import email_validator
from flask_security.forms import unique_user_email
from wtforms import IntegerField
from wtforms.validators import NoneOf
from wtforms.validators import Regexp

from opwen_email_client.util.wtforms import SuffixedStringField
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.config import i8n


# noinspection PyClassHasNoInit
class LoginForm(_LoginForm):
    email = SuffixedStringField(suffix='@{}'.format(AppConfig.CLIENT_EMAIL_HOST))


email_character_validator = Regexp('^[a-zA-Z0-9-.@]*$', message=i8n.EMAIL_CHARACTERS)

forbidden_account_validator = NoneOf(AppConfig.FORBIDDEN_ACCOUNTS, message=i8n.FORBIDDEN_ACCOUNT)


# noinspection PyClassHasNoInit
class RegisterForm(_RegisterForm):
    email = SuffixedStringField(suffix='@{}'.format(AppConfig.CLIENT_EMAIL_HOST),
                                validators=[
                                    email_character_validator,
                                    forbidden_account_validator,
                                    email_required,
                                    email_validator,
                                    unique_user_email,
                                ])

    timezone_offset_minutes = IntegerField(default=0)
