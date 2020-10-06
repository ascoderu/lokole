from pathlib import Path
from typing import Optional

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SubmitField


class RegisterForm(FlaskForm):

    client_id = StringField()
    github_username = StringField()
    github_token = StringField()
    submit = SubmitField()
