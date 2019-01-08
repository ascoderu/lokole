from os import environ
from pathlib import Path

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TextAreaField

from opwen_email_client.util.os import replace_line
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.config import settings_path


class SettingsForm(FlaskForm):
    wvdial = TextAreaField()

    sim_type = StringField()

    submit = SubmitField()

    def update(self):
        restart_required = False
        restart_required |= self._update_wvdial()
        restart_required |= self._update_sim_type()

        if restart_required:
            self._restart_app()

    def _update_wvdial(self) -> bool:
        wvdial = self.wvdial.data.strip()
        if not wvdial:
            return False

        with open(AppConfig.WVDIAL_PATH, 'w') as fobj:
            fobj.write('\n'.join(line.strip()
                                 for line in wvdial.splitlines()))
        return False

    def _update_sim_type(self) -> bool:
        sim_type = self.sim_type.data.strip()
        if sim_type == AppConfig.SIM_TYPE:
            return False

        self._update_config('OPWEN_SIM_TYPE', sim_type)
        return True

    @classmethod
    def _update_config(cls, env_key: str, value: str):
        replace_line(
            settings_path,
            lambda line: line.startswith('{}='.format(env_key)),
            '{}={}'.format(env_key, value))

        config_key = env_key.replace('OPWEN_', '')
        setattr(AppConfig, config_key, value)
        environ[env_key] = value

        return True

    @classmethod
    def _restart_app(cls):
        if AppConfig.RESTART_PATH:
            Path(AppConfig.RESTART_PATH).touch()

    @classmethod
    def from_config(cls):
        try:
            with open(AppConfig.WVDIAL_PATH) as fobj:
                wvdial = fobj.read()
        except OSError:
            wvdial = ''

        return cls(
            wvdial=wvdial,
            sim_type=AppConfig.SIM_TYPE
        )
