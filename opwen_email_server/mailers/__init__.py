from wikipedia import languages
from wikipedia import page
from wikipedia import set_lang

from opwen_email_server.mailers.echo import ECHO_ADDRESS
from opwen_email_server.mailers.echo import EchoEmailFormatter
from opwen_email_server.mailers.wikipedia import WIKIPEDIA_ADDRESS
from opwen_email_server.mailers.wikipedia import WikipediaEmailFormatter

REGISTRY = {
    ECHO_ADDRESS: EchoEmailFormatter(),
    WIKIPEDIA_ADDRESS: WikipediaEmailFormatter(languages, set_lang, page),
}
