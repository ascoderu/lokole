from datetime import datetime
from datetime import timedelta

from flask_testing import TestCase

from opwen_webapp.models import ModelPacker
from utils.testing import AppTestMixin


class TestUser(AppTestMixin, TestCase):
    def test_user_constructor_normalizes_fields(self):
        user = self.new_user(name='FOO', email='FOO@BAR.COM')
        self.assertEqual(user.name, 'foo')
        self.assertEqual(user.email, 'foo@bar.com')


class TestEmail(AppTestMixin, TestCase):
    def test_email_constructor_normalizes_fields(self):
        email = self.new_email(sender='FOO', to=['BAR'])
        self.assertEqual(email.sender, 'foo')
        self.assertEqual(email.to, ['bar'])

    def test_email_with_all_fields_is_complete(self):
        email = self.create_complete_email()
        self.assertTrue(email.is_complete())

    def test_email_must_have_recipient_to_be_complete(self):
        email = self.create_complete_email()
        email.to = []
        self.assertFalse(email.is_complete())

    def test_email_must_have_sender_to_be_complete(self):
        email = self.create_complete_email()
        email.sender = None
        self.assertFalse(email.is_complete())

    def test_email_must_have_date_to_be_complete(self):
        email = self.create_complete_email()
        email.date = None
        self.assertFalse(email.is_complete())

    def test_email_must_have_subject_or_body_to_be_complete(self):
        email = self.create_complete_email()
        email.subject = None
        self.assertTrue(email.is_complete())

        email = self.create_complete_email()
        email.body = None
        self.assertTrue(email.is_complete())

        email = self.create_complete_email()
        email.body = email.subject = None
        self.assertFalse(email.is_complete())

    def test_is_same_as_handles_other_types(self):
        email = self.create_complete_email()
        self.assertFalse(email.is_same_as(None))
        self.assertFalse(email.is_same_as('something'))

    def test_is_same_as(self):
        now = datetime.utcnow()
        email1 = self.create_complete_email(now)
        email2 = self.create_complete_email(now)
        self.assertTrue(email1.is_same_as(email2))

        email2.to = ['other@test.net']
        self.assertFalse(email1.is_same_as(email2))

    def test_is_same_as_must_be_within_same_minute(self):
        now = datetime.utcnow()
        email1 = self.create_complete_email(now)
        email2 = self.create_complete_email(now + timedelta(seconds=10))
        self.assertTrue(email1.is_same_as(email2))

        email2.date = now - timedelta(seconds=10)
        self.assertTrue(email1.is_same_as(email2))

        email2.date = now - timedelta(seconds=60)
        self.assertFalse(email1.is_same_as(email2))

        email2.date = now + timedelta(seconds=60)
        self.assertFalse(email1.is_same_as(email2))


class TestModelPacker(AppTestMixin, TestCase):
    def test_email_packing_roundtrip(self):
        packer = ModelPacker()
        expecteds = [self.create_complete_email() for _ in range(5)]
        actuals = packer.unpack_emails(packer.pack(expecteds))
        for expected, actual in zip(expecteds, actuals):
            self.assertTrue(expected.is_same_as(actual))

    def test_misformed_data_unpacks_gracefully(self):
        packed = {'definitey_not_emails_field': [1, 2]}
        self.assertEqual(ModelPacker().unpack_emails(packed), [])

        packed = {'definitey_not_accounts_field': [1, 2]}
        self.assertEqual(ModelPacker().unpack_accounts(packed), [])
