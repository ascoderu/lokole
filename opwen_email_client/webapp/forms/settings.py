from flask_wtf import FlaskForm
from wtforms import SubmitField
from wtforms import TextAreaField
from wtforms.validators import DataRequired

from opwen_email_client.webapp.config import i8n


class SettingsForm(FlaskForm):
    wvdial = TextAreaField(
        validators=[DataRequired(i8n.WVDIAL_REQUIRED)])

    submit = SubmitField()

    def update_wvdial(self, wvdial_path: str):
        wvdial = self.wvdial.data.splitlines()
        with open(wvdial_path, 'w') as fobj:
            fobj.write('\n'.join(line.strip() for line in wvdial))

    @classmethod
    def with_defaults(cls, wvdial_path: str):
        try:
            with open(wvdial_path) as fobj:
                wvdial = fobj.read()
        except OSError:
            wvdial = ''

        return cls(wvdial=wvdial)
