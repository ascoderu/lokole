from unittest import TestCase

from opwen_email_server.services.auth import EnvironmentAuth


class EnvironmentAuthTest(TestCase):
    def test_parses_clients_from_environment(self):
        auth = EnvironmentAuth(envgetter=lambda _, __: '{"client1":"value1"}')

        self.assertIn("client1", auth)
        self.assertNotIn("client2", auth)

    def test_raises_when_environment_misconfigured(self):
        auth = EnvironmentAuth(envgetter=lambda key, default: default)

        with self.assertRaises(ValueError):
            auth.__contains__('something')
