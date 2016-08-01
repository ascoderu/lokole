from datetime import datetime
from datetime import timedelta

from flask_testing import TestCase

from tests.app_base import AppTestMixin


class TestUser(AppTestMixin, TestCase):
    def test_user_constructor_normalizes_fields(self):
        user = self.new_user(name='FOO', email='FOO@BAR.COM')
        self.assertEqual(user.name, 'foo')
        self.assertEqual(user.email, 'foo@bar.com')


class TestEmail(AppTestMixin, TestCase):
    def test_email_constructor_normalizes_casing(self):
        email = self.new_email(sender='FOO', to=['BAR'])
        self.assertEqual(email.sender, 'foo')
        self.assertEqual(email.to, ['bar'])

    def test_email_constructor_is_xss_safe(self):
        email = self.new_email(body='XSS <script>safe</script>')
        self.assertEqual(email.body, 'XSS safe')

        email = self.new_email(subject='XSS <script>safe</script>')
        self.assertEqual(email.subject, 'XSS safe')

    def test_email_with_all_fields_is_complete(self):
        email = self.create_complete_email()
        self.assertTrue(email.is_complete())

    def test_email_must_have_recipient_to_be_complete(self):
        email = self.create_complete_email(to=[])
        self.assertFalse(email.is_complete())

    def test_email_must_have_sender_to_be_complete(self):
        email = self.create_complete_email(sender=None)
        self.assertFalse(email.is_complete())

    def test_email_must_have_date_to_be_complete(self):
        email = self.create_complete_email(date=None)
        self.assertFalse(email.is_complete())

    def test_email_must_have_subject_or_body_to_be_complete(self):
        email = self.create_complete_email(subject=None)
        self.assertTrue(email.is_complete())

        email = self.create_complete_email(body=None)
        self.assertTrue(email.is_complete())

        email = self.create_complete_email(body=None, subject=None)
        self.assertFalse(email.is_complete())

    # noinspection PyTypeChecker
    def test_is_same_as_handles_other_types(self):
        email = self.create_complete_email()
        self.assertFalse(email.is_same_as(None))
        self.assertFalse(email.is_same_as('something'))

    def test_is_same_as(self):
        now = datetime.utcnow()
        email1 = self.create_complete_email(date=now)
        email2 = self.create_complete_email(date=now)
        self.assertTrue(email1.is_same_as(email2))

        email3 = self.create_complete_email(date=now, to=['other@test.net'])
        self.assertFalse(email1.is_same_as(email3))

    def test_is_same_as_must_be_within_same_minute(self):
        now = datetime.utcnow()
        email1 = self.create_complete_email(date=now)
        email2 = self.create_complete_email(date=now + timedelta(seconds=10))
        self.assertTrue(email1.is_same_as(email2))

        email2.date = now - timedelta(seconds=10)
        self.assertTrue(email1.is_same_as(email2))

        email2.date = now - timedelta(seconds=60)
        self.assertFalse(email1.is_same_as(email2))

        email2.date = now + timedelta(seconds=60)
        self.assertFalse(email1.is_same_as(email2))
