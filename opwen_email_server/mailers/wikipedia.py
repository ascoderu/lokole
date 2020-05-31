from datetime import datetime
from typing import Callable

from wikipedia import languages
from wikipedia import page
from wikipedia import set_lang
from wikipedia.exceptions import DisambiguationError
from wikipedia.exceptions import PageError

from opwen_email_server.utils.log import LogMixin

WIKIPEDIA_ADDRESS = 'wikipedia@bot.lokole.ca'


class WikipediaEmailFormatter(LogMixin):
    def __init__(self, now: Callable[[], datetime] = datetime.utcnow):
        self._now = now

    def __call__(self, email: dict) -> dict:
        language = email['subject']
        if language in languages():
            set_lang(language)
        else:
            set_lang('en')

        try:
            wiki_page = page(email['body'])
        except DisambiguationError as e:
            subject = "Suggested Searches"
            body = "Multiple results found. Try again with the following: \n{}".format('\n'.join(e.options))
        except PageError:
            subject = 'No results'
            body = 'No results found for: {}'.format(email['body'])
        else:
            subject = wiki_page.title
            body = wiki_page.html()

        email['to'] = [email['from']]
        email['from'] = WIKIPEDIA_ADDRESS
        email['sent_at'] = self._now().strftime('%Y-%m-%d %H:%M')
        email['subject'] = subject
        email['body'] = body

        return email
