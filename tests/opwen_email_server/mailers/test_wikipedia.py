from datetime import datetime
from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import MagicMock

from responses import mock as mock_responses
from wikipedia.exceptions import DisambiguationError
from wikipedia.exceptions import PageError

from opwen_email_server.mailers.wikipedia import WikipediaEmailFormatter
from tests.opwen_email_server.helpers import throw


class WikipediaServiceTests(TestCase):
    def setUp(self):
        self.now = datetime.utcnow
        self.languages = MagicMock()
        self.language_setter = Mock()
        self.page_fetch = Mock()

    def test_no_results(self):
        email = {
            'to': ['wikipedia@bot.lokole.ca'], 'from': 'user@lokole.ca', 'subject': 'en', 'body': 'arandomsearch',
            'sent_at': '2020-02-01 21:17'
        }
        self.page_fetch.side_effect = throw(PageError(None, None, None))

        result_email = self._execute_format(email)

        self.assertEqual(result_email['subject'], 'No results')

    def test_multiple_results(self):
        email = {
            'to': ['wikipedia@bot.lokole.ca'], 'from': 'user@lokole.ca', 'subject': 'en', 'body': 'mercury', 'sent_at':
            '2020-02-01 21:17'
        }
        self.page_fetch.side_effect = throw(DisambiguationError(Mock(options=['article1', 'article2']), 'Message'))

        result_email = self._execute_format(email)

        self.assertEqual(result_email['subject'], 'Suggested Searches')

    @mock_responses.activate
    def test_returned_article(self):
        email = {
            'to': ['wikipedia@bot.lokole.ca'], 'from': 'user@lokole.ca', 'subject': 'en', 'body': 'Linear Regression',
            'sent_at': '2020-02-01 21:17'
        }
        self.page_fetch.return_value = Mock(title='Linear regression',
                                            url='https://en.wikipedia.org/wiki/Linear_regression')
        mock_responses.add(mock_responses.GET,
                           'https://en.wikipedia.org/api/rest_v1/page/pdf/Linear_regression',
                           body=b'some bytes',
                           status=200,
                           content_type='application/json')

        result_email = self._execute_format(email)

        self.assertEqual('Linear regression', result_email['subject'])
        self.assertEqual('Linear regression.pdf', result_email['attachments'][0]['filename'])

    def _execute_format(self, *args, **kwargs):
        formatter = WikipediaEmailFormatter(languages_getter=self.languages,
                                            language_setter=self.language_setter,
                                            page_fetch=self.page_fetch)

        return formatter(*args, **kwargs)
