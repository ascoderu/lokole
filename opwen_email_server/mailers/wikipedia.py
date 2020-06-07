from base64 import b64encode
from datetime import datetime
from typing import Callable

from requests import get
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

    def _get_download_link(self, url: str) -> str:
        split_url = url.split('/')
        return 'https://' + split_url[2] + '/api/rest_v1/page/pdf/' + split_url[-1]

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
            body = ''
            download_link = self._get_download_link(wiki_page.url)
            pdf_file = get(download_link)
            email['attachments'] = email['attachments'] = [{
                'filename': subject + '.pdf',
                'content': b64encode(pdf_file.content),
            }]

        email['to'] = [email['from']]
        email['from'] = WIKIPEDIA_ADDRESS
        email['sent_at'] = self._now().strftime('%Y-%m-%d %H:%M')
        email['subject'] = subject
        email['body'] = body

        return email
