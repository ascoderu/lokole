from os import getenv
from pathlib import Path
from shutil import chown

from flask_wtf import FlaskForm
from requests import post
from wtforms import StringField
from wtforms import SubmitField
from wtforms.validators import ValidationError

from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.config import i8n
from opwen_email_client.webapp.tasks import register


class RegisterForm(FlaskForm):

    client_name = StringField()
    github_username = StringField()
    github_token = StringField()
    submit = SubmitField()

    def register_client(self):
        path = self._setup_path()
        self._setup_client(path)

    def _setup_client(self, path):
        name = self.client_name.data.strip()
        token = self.github_token.data.strip()

        endpoint = AppConfig.EMAIL_SERVER_ENDPOINT or 'mailserver.lokole.ca'
        client_domain = '{}.{}'.format(name, 'lokole.ca')
        client_create_url = 'https://{}/api/email/register/'.format(endpoint)

        response = post(client_create_url,
                        json={'domain': client_domain},
                        headers={'Authorization': 'Bearer {}'.format(token)})
        if response.status_code != 200:
            raise ValidationError(i8n.FAILED_REGISTRATION)
        register.delay(name, token, path)

    def _setup_path(self):
        home = Path.home()
        user = home.parts[-1]
        path = (Path(getenv('OPWEN_STATE_DIRECTORY', 'lokole/state')) / 'settings.env').absolute()
        parent = path.parent
        parent.mkdir(parents=True, exist_ok=True)
        is_in_home = parent.parts[:3] == home.parts
        if is_in_home:
            home_parts = parent.parts[3:]
            for part in home_parts:
                home /= part
                chown(str(home), user, user)
        return str(path)
