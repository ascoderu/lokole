from datetime import datetime
from typing import Callable

from opwen_email_server.utils.log import LogMixin

ECHO_ADDRESS = 'echo@bot.lokole.ca'


class EchoEmailFormatter(LogMixin):
    def __init__(self, now: Callable[[], datetime] = datetime.utcnow):
        self._now = now

    def __call__(self, email: dict) -> dict:
        email['to'] = [email['from']]
        email['from'] = ECHO_ADDRESS
        email['sent_at'] = self._now().strftime('%Y-%m-%d %H:%M')
        return email
