from datetime import datetime

from flask_testing import TestCase

from opwen_webapp.controllers import download_remote_updates
from opwen_webapp.controllers import find_attachment
from opwen_webapp.controllers import inbox_emails_for
from opwen_webapp.controllers import new_email_for
from opwen_webapp.controllers import outbox_emails_for
from opwen_webapp.controllers import send_account_finalized_email
from opwen_webapp.controllers import send_welcome_email
from opwen_webapp.controllers import sent_emails_for
from opwen_webapp.controllers import upload_local_updates
from opwen_webapp.controllers import user_exists
from opwen_webapp.models import Email
from opwen_webapp.models import User
from tests.app_base import AppTestMixin


class TestUserExists(AppTestMixin, TestCase):
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


# noinspection PyUnusedLocal,PyPep8Naming
class TestReadEmails(AppTestMixin, TestCase):
    def assertIterablesEqual(self, actual, expected):
        self.assertListEqual(list(actual), list(expected))

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

        self.assertIterablesEqual(actual, expected)

    def test_broken_user_raises_exception(self):
        user = self.new_user(name=None, email=None)

        with self.assertRaises(ValueError):
            sent_emails_for(user)
        with self.assertRaises(ValueError):
            outbox_emails_for(user)

    def test_finds_sent_emails_to_name_or_email(self):
        now = datetime.utcnow()
        user = self.new_user(name='someone', email='someone@test.net')
        expected = [self.new_email(sender=user.name, date=now)]
        not_expected = [self.new_email(sender=user.name)]
        actual = sent_emails_for(user)

        self.assertIterablesEqual(actual, expected)

    def test_finds_outbox_emails_to_name_or_email(self):
        now = datetime.utcnow()
        user = self.new_user(name='someone', email='someone@test.net')
        expected = [self.new_email(sender=user.name)]
        not_expected = [self.new_email(sender=user.name, date=now)]
        actual = outbox_emails_for(user)

        self.assertIterablesEqual(actual, expected)


class TestWriteEmails(AppTestMixin, TestCase):
    def test_creates_new_email_for_local_user(self):
        sender = self.new_user(email='sender@test.net')
        recipient = self.new_user(name='ReciPienT', email='recipient@test.net')
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


# noinspection PyUnusedLocal
class TestRemoteUpload(AppTestMixin, TestCase):
    def _retrieve_uploaded_emails(self, index):
        uploaded = self.app.remote_storage.uploaded[index]
        emails, accounts = self.app.serializer.deserialize(uploaded)
        return emails

    def test_transmits_all_new_emails_without_resending_old_emails(self):
        new_emails = [self.new_email(), self.new_email(), self.new_email()]
        previously_sent_emails = [self.new_email(date=datetime.utcnow())]
        upload_local_updates()

        number_of_upload_calls = len(self.app.remote_storage.uploaded)
        self.assertEqual(number_of_upload_calls, 1)

        uploaded_emails = self._retrieve_uploaded_emails(0)
        for actual, expected in zip(uploaded_emails, new_emails):
            self.assertTrue(actual.is_same_as(expected))

        not_transmitted_emails = Email.query.filter(Email.date.is_(None))
        self.assertEqual(not_transmitted_emails.count(), 0)


class TestRemoteDownload(AppTestMixin, TestCase):
    def _prepare_serialized_data(self, emails, accounts):
        serialized = self.app.serializer.serialize(emails, accounts)
        self.app.remote_storage.downloaded = serialized

    def _prepare_emails_for_download(self, emails):
        self._prepare_serialized_data(emails=emails, accounts=None)

    def _prepare_users_for_download(self, name, email):
        accounts = [self.create_complete_user(name=name, email=email)]
        self._prepare_serialized_data(accounts=accounts, emails=None)

    def test_updates_emails(self):
        remote_emails = [self.create_complete_email_fake() for _ in range(5)]
        self._prepare_emails_for_download(remote_emails)

        download_remote_updates()

        newly_updated_emails = Email.query.all()
        self.assertEqual(len(newly_updated_emails), len(remote_emails))
        for actual, expected in zip(newly_updated_emails, remote_emails):
            self.assertTrue(actual.is_same_as(expected))

    def test_updates_users_on_name(self):
        user, email = self.new_user(name='test'), 'test@opwen.net'
        self._prepare_users_for_download(user.name, email)

        download_remote_updates()

        updated_user = User.query.filter(User.name == user.name).first()
        self.assertIsNotNone(updated_user)
        self.assertEqual(updated_user.email, email)

    def test_updates_users_on_email(self):
        user, email = self.new_user(email='test'), 'test@opwen.net'
        self._prepare_users_for_download(user.email, email)

        download_remote_updates()

        updated_user = User.query.filter(User.name == user.name).first()
        self.assertIsNotNone(updated_user)
        self.assertEqual(updated_user.email, email)

    def test_ignores_corrupted_remote_data(self):
        self.app.remote_storage.downloaded = '/path/does/not/exist'

        download_remote_updates()

        newly_updated_emails = Email.query.all()
        self.assertEqual(len(newly_updated_emails), 0)


# noinspection PyUnusedLocal
class TestFindAttachment(AppTestMixin, TestCase):
    def test_can_access_attachment_from_email(self):
        attachment_path, attachment_name = '/path/to/attachment.txt', 'file.txt'
        user = self.new_user(email='user@test.net')
        email = self.new_email(to=[user.email],
                               attachments=[(attachment_path, attachment_name)])

        attachment = find_attachment(user, attachment_name)

        self.assertEqual(attachment.path, attachment_path)

    def test_cannot_access_attachment_that_does_not_exist(self):
        user = self.new_user(email='user@test.net')
        email = self.new_email(to=[user.email],
                               attachments=[('/path/to/file.txt', 'file.txt')])

        attachment = find_attachment(user, 'other-thing.txt')

        self.assertIsNone(attachment)

    def test_cannot_access_attachment_from_email_to_another_user(self):
        attachment_path, attachment_name = '/path/to/file.txt', 'file.txt'
        other_user = self.new_user(email='other_user@test.net')
        owner_user = self.new_user(email='owner_user@test.net')
        email = self.new_email(to=[owner_user.email],
                               attachments=[(attachment_path, attachment_name)])

        other_lookup = find_attachment(other_user, attachment_name)
        owner_lookup = find_attachment(owner_user, attachment_name)

        self.assertIsNone(other_lookup)
        self.assertEqual(owner_lookup.path, attachment_path)


# noinspection PyPep8Naming
class TestUserLifecycleAutomatedEmails(AppTestMixin, TestCase):
    def assertEmailWasSentTo(self, user):
        email = inbox_emails_for(user).first()
        self.assertIsNotNone(email)
        self.assertTrue(email.date)
        self.assertTrue(email.sender)
        self.assertTrue(email.body)
        self.assertTrue(email.subject)

    def test_welcome_email_is_sent(self):
        user = self.new_user(name='Felix')

        send_welcome_email(user)

        self.assertEmailWasSentTo(user)

    def test_acccount_finalized_email_is_sent(self):
        user = self.new_user(name='Felix', email='felix@ascoderu.ca')

        send_account_finalized_email(user)

        self.assertEmailWasSentTo(user)
