from opwen_email_server.mailers.echo import ECHO_ADDRESS
from opwen_email_server.mailers.echo import EchoEmailFormatter

REGISTRY = {
    ECHO_ADDRESS: EchoEmailFormatter(),
}
