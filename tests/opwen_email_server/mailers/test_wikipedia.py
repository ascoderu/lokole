from unittest import TestCase

import responses

from opwen_email_server.mailers.wikipedia import WikipediaEmailFormatter


class WikipediaServiceTests(TestCase):
    def setUp(self):
        self._formatter = WikipediaEmailFormatter()

    def test_no_results(self):
        email = {
            'to': ['wikipedia@bot.lokole.ca'], 'from': 'user@lokole.ca', 'subject': 'en', 'body': 'arandomsearch',
            'sent_at': '2020-02-01 21:17'
        }
        result_email = self._formatter(email)
        self.assertTrue(result_email['subject'] == 'No results')

    def test_multiple_results(self):
        email = {
            'to': ['wikipedia@bot.lokole.ca'], 'from': 'user@lokole.ca', 'subject': 'en', 'body': 'mercury', 'sent_at':
            '2020-02-01 21:17'
        }
        result_email = self._formatter(email)
        self.assertTrue(result_email['subject'] == 'Suggested Searches')

    def test_returned_article(self):
        email = {
            'to': ['wikipedia@bot.lokole.ca'], 'from': 'user@lokole.ca', 'subject': 'en', 'body': 'Linear Regression',
            'sent_at': '2020-02-01 21:17'
        }
        with responses.RequestsMock(passthru_prefixes='http://en.wikipedia.org/w/') as res:
            res.add(responses.GET,
                    url='https://en.wikipedia.org/api/rest_v1/page/pdf/Linear_regression',
                    body=b'some bytes',
                    status=200,
                    content_type='application/json')
            result_email = self._formatter(email)
            self.assertEqual('Linear regression', result_email['subject'])
            self.assertEqual('Linear regression.pdf', result_email['attachments'][0]['filename'])
