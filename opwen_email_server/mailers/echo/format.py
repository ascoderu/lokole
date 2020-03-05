from opwen_email_server.utils.log import LogMixin

ECHO_ADRESS = 'echo@bot.lokole.ca'


class EchoEmailFormatter(LogMixin):
    def _format_echo_email(self, email: dict) -> dict:
        email['to'] = email['from']
        email['from'] = ECHO_ADRESS
        return email

    def __call__(self, parsed_email: dict) -> dict:
        return self._format_echo_email(parsed_email)
