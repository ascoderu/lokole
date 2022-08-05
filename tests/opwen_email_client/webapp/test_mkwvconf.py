from json import loads
from os.path import isfile
from unittest import skipUnless

from mkwvconf.mkwvconf import DEFAULT_XML_PATH

from tests.opwen_email_client.webapp.base import Base


@skipUnless(isfile(DEFAULT_XML_PATH), reason='mkwvconf database is missing')
class MkwvconfTests(Base.AppTests):
    def get_json(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return loads(response.get_data().decode('utf-8'))

    def test_list_countries(self):
        response = self.get_json('/api/mkwvconf/')
        self.assertIn('ae', response['countries'])

    def test_list_providers(self):
        response = self.get_json('/api/mkwvconf/ae')
        self.assertIn('Etisalat', response['providers'])

    def test_list_apns(self):
        response = self.get_json('/api/mkwvconf/ae/Etisalat')
        self.assertIn('mnet', response['apns'])

    def test_get_config(self):
        response = self.get_json('/api/mkwvconf/ae/Etisalat/mnet')
        self.assertIn('Username = mnet\n', response['config'])
