from datetime import datetime
from typing import Callable
from urllib.parse import urlparse

from requests import get
from wikipedia import WikipediaPage
from wikipedia import languages
from wikipedia import page
from wikipedia import set_lang
from wikipedia.exceptions import DisambiguationError
from wikipedia.exceptions import PageError

from opwen_email_server.utils.log import LogMixin

WIKIPEDIA_ADDRESS = 'wikipedia@bot.lokole.ca'


class WikipediaEmailFormatter(LogMixin):
    def __init__(self,
                 languages_getter: Callable[[], dict] = languages,
                 language_setter: Callable[[str], None] = set_lang,
                 page_fetch: Callable[[str], WikipediaPage] = page,
                 now: Callable[[], datetime] = datetime.utcnow):
        self._now = now
        self._languages = languages_getter
        self._language_setter = language_setter
        self._page_fetch = page_fetch

    def _get_download_link(self, url: str) -> str:
        parsed_url = urlparse(url)
        return parsed_url.scheme + '://' + parsed_url.netloc + '/api/rest_v1/page/pdf/' + parsed_url.path.split('/')[-1]

    def __call__(self, email: dict) -> dict:
        language = email['subject']
        if language in self._languages():
            self._language_setter(language)
        else:
            self._language_setter('en')

        try:
            wiki_page = self._page_fetch(email['body'].strip())
        except DisambiguationError as e:
            subject = 'Suggested Searches'
            body = 'Multiple results found. Try again with the following: \n{}'.format('\n'.join(e.options))
        except PageError:
            subject = 'No results'
            body = 'No results found for: {}'.format(email['body'])
        else:
            subject = wiki_page.title
            body = 'Results found'
            download_link = self._get_download_link(wiki_page.url)
            pdf_file = get(download_link)
            email['attachments'] = [{
                'filename': subject + '.pdf',
                'content': pdf_file.content,
            }]

        email['to'] = [email['from']]
        email['from'] = WIKIPEDIA_ADDRESS
        email['sent_at'] = self._now().strftime('%Y-%m-%d %H:%M')
        email['subject'] = subject
        email['body'] = body

        return email
