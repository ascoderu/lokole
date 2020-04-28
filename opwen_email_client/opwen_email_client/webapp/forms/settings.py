from os import environ
from pathlib import Path
from typing import Optional

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TextAreaField

from opwen_email_client import __version__
from opwen_email_client.util.os import replace_line
from opwen_email_client.util.wtforms import CronSchedule
from opwen_email_client.webapp.actions import RestartApp
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.config import i8n
from opwen_email_client.webapp.config import settings_path
from opwen_email_client.webapp.tasks import update


class SettingsForm(FlaskForm):
    wvdial = TextAreaField()

    code_version = StringField()

    sim_type = StringField()

    sync_schedule = StringField(validators=[CronSchedule()], description=i8n.SYNC_SCHEDULE_SYNTAX_DESCRIPTION)

    submit = SubmitField()

    def update(self):
        restart_required = False
        restart_required |= self._update_sim_type()
        restart_required |= self._update_sync_schedule()
        restart_required |= self._update_wvdial()
        restart_required |= self._update_code_version()

        if restart_required:
            restart_app = RestartApp(restart_paths=AppConfig.RESTART_PATHS)
            restart_app()

    def _update_wvdial(self) -> bool:
        wvdial = self.wvdial.data.strip()
        path = _get_wvdial_path(self.sim_type.data.strip())
        if not wvdial or wvdial == _read_wvdial(path):
            return False

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open('w', encoding='utf-8') as fobj:
            fobj.write('\n'.join(line.strip() for line in wvdial.splitlines()))
        return False

    def _update_code_version(self) -> bool:
        code_version = self.code_version.data.strip()
        if not code_version or code_version == __version__:
            return False

        update.delay(version=code_version)
        return False

    def _update_sim_type(self) -> bool:
        sim_type = self.sim_type.data.strip()
        if not sim_type or sim_type == AppConfig.SIM_TYPE:
            return False

        self._update_config('OPWEN_SIM_TYPE', sim_type)
        return True

    def _update_sync_schedule(self) -> bool:
        sync_schedule = self.sync_schedule.data.strip()
        if sync_schedule == AppConfig.SYNC_SCHEDULE:
            return False

        self._update_config('OPWEN_SYNC_SCHEDULE', sync_schedule)
        return True

    @classmethod
    def _update_config(cls, env_key: str, value: str):
        def is_env(line):
            return line.startswith('{}='.format(env_key))

        replace_line(settings_path, is_env, '{}={}'.format(env_key, value))

        config_key = env_key.replace('OPWEN_', '')
        setattr(AppConfig, config_key, value)
        environ[env_key] = value

        return True

    @classmethod
    def from_config(cls):
        return cls(
            code_version=__version__,
            wvdial=_read_wvdial(_get_wvdial_path()),
            sync_schedule=AppConfig.SYNC_SCHEDULE,
            sim_type=AppConfig.SIM_TYPE,
        )


def _get_wvdial_path(sim_type: Optional[str] = AppConfig.SIM_TYPE) -> Path:
    return Path(AppConfig.SIM_CONFIG_DIR) / sim_type


def _read_wvdial(path: Path) -> str:
    if not path.is_file():
        return ''

    with path.open(encoding='utf-8') as fobj:
        return fobj.read().strip()
