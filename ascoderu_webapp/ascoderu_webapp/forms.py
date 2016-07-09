from flask_security import LoginForm as BaseLoginForm
from flask_security import RegisterForm as BaseRegisterForm
from wtforms import StringField
from wtforms.validators import DataRequired


class LoginForm(BaseLoginForm):
    email = StringField('Name or Email', [DataRequired()])


class RegisterForm(BaseRegisterForm):
    email = StringField('Name', [DataRequired()])
