from typing import Optional

from opwen_email_server.utils.log import LogMixin

ECHO_ADRESS = 'echo@bot.lokole.ca'


class EmailFormatter(LogMixin):
    def format_echo_email(self, email: dict) -> dict:
        email['to'] = email['from']
        email['from'] = ECHO_ADRESS
        return email

    def __call__(self, parsed_email: dict) -> Optional[dict]:
        if parsed_email['to'] == ECHO_ADRESS:
            return self._format_echo_email(parsed_email)
        else:
            return None
