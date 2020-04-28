from tests.opwen_email_client.webapp.base import Base


class ViewTests(Base.AppTests):
    def test_app_starts(self):
        response = self.client.get('/')
        self.assertTrue(response)
