from flask_login import login_required as _login_required
from flask_security import Security

from opwen_email_client.webapp.config import AppConfig

security = Security()


def login_required(func):
    if AppConfig.TESTING:
        return func

    return _login_required(func)
