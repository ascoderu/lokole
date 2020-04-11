from opwen_email_server.mailers.echo.format import EchoEmailFormatter

ECHO_ADDRESS = 'echo@bot.lokole.ca'

REGISTRY = {
    ECHO_ADDRESS: EchoEmailFormatter(),
}
