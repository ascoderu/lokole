from os import getenv
from os import getuid
from json import dumps
from pathlib import Path
from pwd import getpwuid
from shutil import chown

from flask_wtf import FlaskForm
from requests import post
from wtforms import StringField
from wtforms import SubmitField

from opwen_email_client.webapp.actions import ClientRegister
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.config import root_domain
from opwen_email_client.webapp.tasks import register


class RegisterForm(FlaskForm):

    client_name = StringField()
    github_username = StringField()
    github_token = StringField()
    submit = SubmitField()

    def register(self):
        path = self._setup_path()
        self._setup_client(path)

    def _setup_client(self, path):
        name = self.client_name.data.strip()
        username = self.github_username.data.strip()
        token = self.github_token.data.strip()

        client_domain = '{}.{}'.format(name, 'lokole.ca')
        client_create_url = 'https://{}/api/email/register/'.format('mailserver.lokole.ca')
        create_request_payload = dumps({'domain': client_domain}).encode('utf-8')
        create_headers = {'Content-Type': 'application/json',
                          'Content-Length': str(len(create_request_payload)),
                          'Authorization': 'Bearer {}'.format(token)}

        response = post(client_create_url, data=create_request_payload, headers=create_headers)
        response.raise_for_status()

    def _setup_path(self):
        home = Path.home()
        user = home.parts[-1]
        path = (Path(getenv('LOKOLE_STATE_DIRECTORY', 'lokole/state')) / 'settings.env').absolute()
        parent = path.parent
        parent.mkdir(parents=True, exist_ok=True)
        is_in_home = parent.parts[:3] == home.parts
        if is_in_home:
            home_parts = parent.parts[3:]
            for part in home_parts:
                home /= part
                chown(str(home), user, user)
        return str(path)
