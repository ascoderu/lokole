from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import MagicMock
from uuid import uuid4

from opwen_email_server import actions


class PingTests(TestCase):
    def test_200(self):
        action = actions.Ping()
        message, status = action()
        self.assertEqual(status, 200)


# noinspection PyTypeChecker
class SendOutboundEmailsTests(TestCase):
    def setUp(self):
        self.email_storage = Mock()
        self.email_sender = Mock()

    def test_200(self):
        resource_id = str(uuid4())
        email = {'subject': 'test'}

        self.email_storage.fetch_object.return_value = email
        self.email_sender.send_email.return_value = True

        action = actions.SendOutboundEmails(self.email_storage, self.email_sender)
        _, status = action(resource_id)

        self.assertEqual(status, 200)
        self.email_storage.fetch_object.assert_called_once_with(resource_id)
        self.email_sender.send_email.assert_called_once_with(email)

    def test_500(self):
        resource_id = str(uuid4())
        email = {'subject': 'test'}

        self.email_storage.fetch_object.return_value = email
        self.email_sender.send_email.return_value = False

        action = actions.SendOutboundEmails(self.email_storage, self.email_sender)
        _, status = action(resource_id)

        self.assertEqual(status, 500)
        self.email_storage.fetch_object.assert_called_once_with(resource_id)
        self.email_sender.send_email.assert_called_once_with(email)


# noinspection PyTypeChecker
class StoreInboundEmailsTests(TestCase):
    def setUp(self):
        self.raw_email_storage = Mock()
        self.email_storage = Mock()
        self.pending_storage = Mock()
        self.pending_factory = MagicMock()
        self.email_parser = MagicMock()

    def test_200(self):
        resource_id = str(uuid4())
        domain = 'test.com'
        raw_email = 'dummy-mime'
        email = {'to': ['foo@{}'.format(domain)], '_uid': resource_id}

        self.raw_email_storage.fetch_text.return_value = raw_email
        self.pending_factory.return_value = self.pending_storage
        self.email_parser.return_value = email

        action = actions.StoreInboundEmails(self.raw_email_storage, self.email_storage, self.pending_factory, self.email_parser)
        _, status = action(resource_id)

        self.assertEqual(status, 200)
        self.raw_email_storage.fetch_text.assert_called_once_with(resource_id)
        self.raw_email_storage.delete.assert_called_once_with(resource_id)
        self.email_storage.store_object.assert_called_once_with(resource_id, email)
        self.pending_factory.assert_called_once_with(domain)
        self.pending_storage.store_text.assert_called_once_with(resource_id, 'pending')
        self.email_parser.assert_called_once_with(raw_email)


# noinspection PyTypeChecker
class StoreWrittenClientEmailsTests(TestCase):
    def setUp(self):
        self.client_storage = Mock()
        self.email_storage = Mock()
        self.next_task = MagicMock()

    def test_200(self):
        resource_id = str(uuid4())
        email_id = str(uuid4())
        email = {'from': 'foo@test.com', '_uid': email_id}

        self.client_storage.fetch_objects.return_value = [email]

        action = actions.StoreWrittenClientEmails(self.client_storage, self.email_storage, self.next_task)
        _, status = action(resource_id)

        self.assertEqual(status, 200)
        self.client_storage.fetch_objects.assert_called_once_with(resource_id)
        self.email_storage.store_object.assert_called_once_with(email_id, email)
        self.next_task.assert_called_once_with(email_id)
        self.client_storage.delete.assert_called_once_with(resource_id)


# noinspection PyTypeChecker
class ReceiveInboundEmailTests(TestCase):
    def setUp(self):
        self.auth = Mock()
        self.raw_email_storage = Mock()
        self.next_task = MagicMock()
        self.email_id_source = MagicMock()

    def test_403(self):
        client_id = str(uuid4())
        domain = None
        email = 'dummy-mime'

        self.auth.domain_for.return_value = domain

        action = actions.ReceiveInboundEmail(self.auth, self.raw_email_storage, self.next_task, self.email_id_source)
        _, status = action(client_id, email)

        self.assertEqual(status, 403)
        self.auth.domain_for.assert_called_once_with(client_id)

    def test_200(self):
        client_id = str(uuid4())
        email_id = str(uuid4())
        domain = 'test.com'
        email = 'dummy-mime'

        self.auth.domain_for.return_value = domain
        self.email_id_source.return_value = email_id

        action = actions.ReceiveInboundEmail(self.auth, self.raw_email_storage, self.next_task, self.email_id_source)
        _, status = action(client_id, email)

        self.assertEqual(status, 200)
        self.auth.domain_for.assert_called_once_with(client_id)
        self.email_id_source.assert_called_once_with()
        self.raw_email_storage.store_text.assert_called_once_with(email_id, email)
        self.next_task.assert_called_once_with(email_id)


# noinspection PyTypeChecker
class DownloadClientEmailsTests(TestCase):
    def setUp(self):
        self.auth = Mock()
        self.client_storage = Mock()
        self.email_storage = Mock()
        self.pending_factory = MagicMock()
        self.pending_storage = Mock()

    def test_403(self):
        client_id = str(uuid4())
        domain = None

        self.auth.domain_for.return_value = domain

        action = actions.DownloadClientEmails(self.auth, self.client_storage, self.email_storage, self.pending_factory)
        _, status = action(client_id)

        self.assertEqual(status, 403)
        self.auth.domain_for.assert_called_once_with(client_id)

    def test_200(self):
        client_id = str(uuid4())
        email_id = str(uuid4())
        resource_id = str(uuid4())
        domain = 'test.com'
        email = {'_uid': email_id}

        _stored = []

        def store_objects_mock(emails):
            _stored.extend(emails)
            return resource_id

        self.auth.domain_for.return_value = domain
        self.pending_factory.return_value = self.pending_storage
        self.pending_storage.iter.return_value = [email_id]
        self.email_storage.fetch_object.return_value = email
        self.client_storage.store_objects.side_effect = store_objects_mock

        action = actions.DownloadClientEmails(self.auth, self.client_storage, self.email_storage, self.pending_factory)
        response = action(client_id)

        self.assertEqual(response.get('resource_id'), resource_id)
        self.auth.domain_for.assert_called_once_with(client_id)
        self.pending_factory.assert_called_once_with(domain)
        self.pending_storage.iter.assert_called_once_with()
        self.pending_storage.delete.assert_called_once_with(email_id)
        self.email_storage.fetch_object.assert_called_once_with(email_id)
        self.assertEqual(_stored, [email])


# noinspection PyTypeChecker
class UploadClientEmailsTests(TestCase):
    def setUp(self):
        self.auth = Mock()
        self.next_task = MagicMock()

    def test_403(self):
        client_id = str(uuid4())
        domain = None
        upload_info = {}

        self.auth.domain_for.return_value = domain

        action = actions.UploadClientEmails(self.auth, self.next_task)
        _, status = action(client_id, upload_info)

        self.assertEqual(status, 403)
        self.auth.domain_for.assert_called_once_with(client_id)

    def test_200(self):
        client_id = str(uuid4())
        resource_id = str(uuid4())
        domain = 'test.com'
        upload_info = {'resource_id': resource_id}

        self.auth.domain_for.return_value = domain

        action = actions.UploadClientEmails(self.auth, self.next_task)
        _, status = action(client_id, upload_info)

        self.assertEqual(status, 200)
        self.auth.domain_for.assert_called_once_with(client_id)
        self.next_task.assert_called_once_with(resource_id)


# noinspection PyTypeChecker
class RegisterClientTests(TestCase):
    def setUp(self):
        self.auth = Mock()
        self.client_id_source = MagicMock()
        self.setup_email_dns = MagicMock()

    def test_200(self):
        client_id = str(uuid4())
        client_storage_account = 'account'
        client_storage_key = 'key'
        domain = 'test.com'

        self.client_id_source.return_value = client_id

        action = actions.RegisterClient(self.auth, client_storage_account, client_storage_key, self.setup_email_dns, self.client_id_source)
        response = action({'domain': domain})

        self.assertEqual(response['client_id'], client_id)
        self.assertEqual(response['storage_account'], client_storage_account)
        self.assertEqual(response['storage_key'], client_storage_key)
        self.auth.insert.assert_called_once_with(client_id, domain)
        self.setup_email_dns.assert_called_once_with(client_id, domain)
