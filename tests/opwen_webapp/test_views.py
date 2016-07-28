from flask import request
from flask_testing import TestCase

from tests.base import AppTestMixin


class TestLoginRequiredViews(AppTestMixin, TestCase):
    LOGIN_REQUIRED_ENDPOINTS = ['/email/sent', '/email/inbox', '/email/outbox']

    def test_private_endpoints_disallow_not_logged_in_user(self):
        with self.app.test_client() as client:
            for endpoint in self.LOGIN_REQUIRED_ENDPOINTS:
                client.get(endpoint, follow_redirects=True)
                self.assertEqual(request.endpoint, 'security.login')
