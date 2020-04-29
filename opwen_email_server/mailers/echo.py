from opwen_email_server.utils.log import LogMixin

ECHO_ADDRESS = 'echo@bot.lokole.ca'


class EchoEmailFormatter(LogMixin):
    def __call__(self, email: dict) -> dict:
        email['to'] = [email['from']]
        email['from'] = ECHO_ADDRESS
        return email
