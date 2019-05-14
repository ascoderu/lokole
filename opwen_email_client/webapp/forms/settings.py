from os import environ
from pathlib import Path
from typing import Optional
from typing import Tuple

from crontab import CronItem
from crontab import CronTab
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TextAreaField

from opwen_email_client.util.os import replace_line
from opwen_email_client.util.wtforms import CronSchedule
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.config import i8n
from opwen_email_client.webapp.config import settings_path


class SettingsForm(FlaskForm):
    wvdial = TextAreaField()

    sim_type = StringField()

    sync_schedule = StringField(
        validators=[CronSchedule()],
        description=i8n.SYNC_SCHEDULE_SYNTAX_DESCRIPTION)

    submit = SubmitField()

    def update(self):
        restart_required = False
        restart_required |= self._update_sim_type()
        restart_required |= self._update_sync_schedule()
        restart_required |= self._update_wvdial()

        if restart_required:
            self._restart_app()

    def _update_wvdial(self) -> bool:
        wvdial = self.wvdial.data.strip()
        path = _get_wvdial_path(self.sim_type.data.strip())
        if not wvdial or wvdial == _read_wvdial(path):
            return False

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open('w', encoding='utf-8') as fobj:
            fobj.write('\n'.join(line.strip()
                                 for line in wvdial.splitlines()))
        return False

    def _update_sim_type(self) -> bool:
        sim_type = self.sim_type.data.strip()
        if not sim_type or sim_type == AppConfig.SIM_TYPE:
            return False

        self._update_config('OPWEN_SIM_TYPE', sim_type)
        return True

    def _update_sync_schedule(self) -> bool:
        sync_schedule = self.sync_schedule.data.strip()
        if sync_schedule == _get_sync_schedule():
            return False

        cron, job = _get_sync_cron()
        if not job:
            job = cron.new(AppConfig.SYNC_SCRIPT)

        if sync_schedule:
            job.setall(sync_schedule)
        else:
            cron.remove_all(command=AppConfig.SYNC_SCRIPT)

        cron.write()
        return False

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
        for path in AppConfig.RESTART_PATHS:
            Path(path).touch()

    @classmethod
    def from_config(cls):
        return cls(
            wvdial=_read_wvdial(_get_wvdial_path()),
            sync_schedule=_get_sync_schedule(),
            sim_type=AppConfig.SIM_TYPE
        )


def _get_sync_schedule() -> str:
    _, job = _get_sync_cron()
    schedule = ' '.join(str(entry) for entry in job.slices) if job else ''
    return schedule


def _get_sync_cron() -> Tuple[CronTab, Optional[CronItem]]:
    cron = CronTab(user=True)

    try:
        job = next(cron.find_command(AppConfig.SYNC_SCRIPT))
    except StopIteration:
        job = None

    return cron, job


def _get_wvdial_path(sim_type: Optional[str] = AppConfig.SIM_TYPE) -> Path:
    return Path(AppConfig.SIM_CONFIG_DIR) / sim_type


def _read_wvdial(path: Path) -> str:
    if not path.is_file():
        return ''

    with path.open(encoding='utf-8') as fobj:
        return fobj.read().strip()
