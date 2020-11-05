from os import getenv
from os import getuid
from pathlib import Path
from pwd import getpwuid
from shutil import chown

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SubmitField

from opwen_email_client.webapp.actions import ClientRegister
from opwen_email_client.webapp.actions import RestartApp
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.config import root_domain


class RegisterForm(FlaskForm):

    client_name = StringField()
    github_username = StringField()
    github_token = StringField()
    submit = SubmitField()

    def register(self):
        registration_details = self._setup_client()
        opwen_settings = self._fetch_settings()
        path = self._setup_path()
        self._write_settings_to_file(path, opwen_settings, registration_details)
        self._restart()

    def _setup_client(self):
        name = self.client_name.data.strip()
        username = self.github_username.data.strip()
        token = self.github_token.data.strip()
        register = ClientRegister(name, username, token, None)
        client_details = register()
        return client_details

    def _fetch_settings(self):
        if AppConfig.RESTART_PATHS:
            restart_paths_list = ['{}={}'.format(key, value) for (key, value) in
                                    AppConfig.RESTART_PATHS.items()]
            restart_path = ','.join(restart_paths_list)
        else:
            restart_path = ''

        return {
            'OPWEN_APP_ROOT': AppConfig.APP_ROOT,
            'OPWEN_STATE_DIRECTORY': AppConfig.STATE_BASEDIR,
            'OPWEN_SESSION_KEY': AppConfig.SECRET_KEY,
            'OPWEN_MAX_UPLOAD_SIZE_MB': AppConfig.MAX_UPLOAD_SIZE_MB,
            'OPWEN_SIM_TYPE': AppConfig.SIM_TYPE,
            'OPWEN_EMAIL_SERVER_HOSTNAME': AppConfig.EMAIL_SERVER_HOSTNAME,
            'OPWEN_CLIENT_NAME': self.client_name.data.strip(),
            'OPWEN_ROOT_DOMAIN': root_domain,
            'OPWEN_RESTART_PATH': restart_path,
        }

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

    def _write_settings_to_file(self, path, client_settings, client_details):
        client_settings_list = ['{}={}'.format(key, value) for (key, value) in
                                client_settings.items()]
        client_details_list = ['{}={}'.format(key, value) for (key, value) in
                                client_details.items()]

        with open(path, 'w') as fobj:
            fobj.write('\n'.join(client_settings_list))
            fobj.write('\n'.join(client_details_list))

    def _restart(self):
        restart_app = RestartApp(restart_paths=AppConfig.RESTART_PATHS)
        restart_app()
