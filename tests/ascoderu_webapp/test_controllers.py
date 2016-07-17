from datetime import datetime

from flask_testing import TestCase

from ascoderu_webapp.controllers import inbox_emails_for
from ascoderu_webapp.controllers import new_email_for
from ascoderu_webapp.controllers import outbox_emails_for
from ascoderu_webapp.controllers import sent_emails_for
from ascoderu_webapp.controllers import user_exists
from ascoderu_webapp.models import Email
from utils.testing import AppTestMixin


class TestUserExists(AppTestMixin, TestCase):
    def test_returns_false_for_invalid_argument(self):
        self.assertFalse(user_exists(None))
        self.assertFalse(user_exists(''))

    def test_finds_user_by_name(self):
        name = 'some-name'
        self.new_user(name=name)

        self.assertTrue(user_exists(name))
        self.assertTrue(user_exists(name.upper()))

    def test_finds_user_by_email(self):
        email = 'someone@email.net'
        self.new_user(email=email)

        self.assertTrue(user_exists(email))
        self.assertTrue(user_exists(email.upper()))

    def test_does_not_find_non_existing_user(self):
        existing_name = 'some-name'
        non_existing_name = 'does-not-exist'
        self.new_user(name=existing_name)

        self.assertFalse(user_exists(non_existing_name))


# noinspection PyUnusedLocal
class TestReadEmails(AppTestMixin, TestCase):
    def test_finds_inbox_emails_to_name_or_email(self):
        user = self.new_user(name='someone', email='someone@test.net')
        other_user = self.new_user(name='otherone', email='otherone@test.net')
        expected = [self.new_email(to=[user.name]),
                    self.new_email(to=[user.name.upper()]),
                    self.new_email(to=[user.email]),
                    self.new_email(to=[user.email.upper()]),
                    self.new_email(to=[user.name, other_user.name]),
                    self.new_email(to=[user.email, user.name]),
                    self.new_email(to=[user.email, user.email]),
                    self.new_email(to=[user.email, user.name, other_user.name])]
        not_expected = [self.new_email(to=[other_user.name]),
                        self.new_email(to=[other_user.email]),
                        self.new_email(to=[other_user.name.upper()])]
        actual = inbox_emails_for(user)

        self.assertSequenceEqual(actual, expected)

    def test_finds_sent_emails_to_name_or_email(self):
        now = datetime.utcnow()
        user = self.new_user(name='someone', email='someone@test.net')
        expected = [self.new_email(sender=user.name, date=now)]
        not_expected = [self.new_email(sender=user.name)]
        actual = sent_emails_for(user)

        self.assertSequenceEqual(actual, expected)

    def test_finds_outbox_emails_to_name_or_email(self):
        now = datetime.utcnow()
        user = self.new_user(name='someone', email='someone@test.net')
        expected = [self.new_email(sender=user.name)]
        not_expected = [self.new_email(sender=user.name, date=now)]
        actual = outbox_emails_for(user)

        self.assertSequenceEqual(actual, expected)


class TestWriteEmails(AppTestMixin, TestCase):
    def test_creates_new_email_for_local_user(self):
        sender = self.new_user(email='sender@test.net')
        recipient = self.new_user(name='recipient', email='recipient@test.net')
        new_email_for(sender, recipient.name, 'subject', 'body')
        email = next(iter(Email.query.all()), None)

        self.assertIsNotNone(email)
        self.assertEqual(sender.email, email.sender)
        self.assertIn(recipient.name, email.to)
        self.assertEqual((datetime.utcnow() - email.date).days, 0)

    def test_creates_new_email_for_remote_user(self):
        sender = self.new_user(email='sender@test.net')
        recipient = 'recipient@test.net'
        new_email_for(sender, recipient, 'subject', 'body')
        email = next(iter(Email.query.all()), None)

        self.assertIsNotNone(email)
        self.assertEqual(sender.email, email.sender)
        self.assertIn(recipient, email.to)
        self.assertIsNone(email.date)

