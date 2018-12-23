from collections import defaultdict
from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import Mock
from uuid import uuid4

from opwen_email_server import actions
from opwen_email_server.constants import sync
from opwen_email_server.services.storage import AccessInfo


class PingTests(TestCase):
    def test_200(self):
        action = actions.Ping()
        message, status = action()
        self.assertEqual(status, 200)


# noinspection PyTypeChecker
class SendOutboundEmailsTests(TestCase):
    def setUp(self):
        self.email_storage = Mock()
        self.send_email = MagicMock()

    def test_200(self):
        resource_id = str(uuid4())
        email = {'subject': 'test'}

        self.email_storage.fetch_object.return_value = email
        self.send_email.return_value = True

        _, status = self._execute_action(resource_id)

        self.assertEqual(status, 200)
        self.email_storage.fetch_object.assert_called_once_with(resource_id)
        self.send_email.assert_called_once_with(email)

    def test_500(self):
        resource_id = str(uuid4())
        email = {'subject': 'test'}

        self.email_storage.fetch_object.return_value = email
        self.send_email.return_value = False

        _, status = self._execute_action(resource_id)

        self.assertEqual(status, 500)
        self.email_storage.fetch_object.assert_called_once_with(resource_id)
        self.send_email.assert_called_once_with(email)

    def _execute_action(self, *args, **kwargs):
        action = actions.SendOutboundEmails(
            email_storage=self.email_storage,
            send_email=self.send_email)

        return action(*args, **kwargs)


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

        _, status = self._execute_action(resource_id)

        self.assertEqual(status, 200)
        self.raw_email_storage.fetch_text.assert_called_once_with(resource_id)
        self.raw_email_storage.delete.assert_called_once_with(resource_id)
        self.email_storage.store_object.assert_called_once_with(resource_id, email)
        self.pending_factory.assert_called_once_with(domain)
        self.pending_storage.store_text.assert_called_once_with(resource_id, 'pending')
        self.email_parser.assert_called_once_with(raw_email)

    def _execute_action(self, *args, **kwargs):
        action = actions.StoreInboundEmails(
            raw_email_storage=self.raw_email_storage,
            email_storage=self.email_storage,
            pending_factory=self.pending_factory,
            email_parser=self.email_parser)

        return action(*args, **kwargs)


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

        _, status = self._execute_action(resource_id)

        self.assertEqual(status, 200)
        self.client_storage.fetch_objects.assert_called_once_with(resource_id, sync.EMAILS_FILE)
        self.email_storage.store_object.assert_called_once_with(email_id, email)
        self.next_task.assert_called_once_with(email_id)
        self.client_storage.delete.assert_called_once_with(resource_id)

    def _execute_action(self, *args, **kwargs):
        action = actions.StoreWrittenClientEmails(
            client_storage=self.client_storage,
            email_storage=self.email_storage,
            next_task=self.next_task)

        return action(*args, **kwargs)


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

        _, status = self._execute_action(client_id, email)

        self.assertEqual(status, 403)
        self.auth.domain_for.assert_called_once_with(client_id)

    def test_200(self):
        client_id = str(uuid4())
        email_id = str(uuid4())
        domain = 'test.com'
        email = 'dummy-mime'

        self.auth.domain_for.return_value = domain
        self.email_id_source.return_value = email_id

        _, status = self._execute_action(client_id, email)

        self.assertEqual(status, 200)
        self.auth.domain_for.assert_called_once_with(client_id)
        self.email_id_source.assert_called_once_with()
        self.raw_email_storage.store_text.assert_called_once_with(email_id, email)
        self.next_task.assert_called_once_with(email_id)

    def _execute_action(self, *args, **kwargs):
        action = actions.ReceiveInboundEmail(
            auth=self.auth,
            raw_email_storage=self.raw_email_storage,
            next_task=self.next_task,
            email_id_source=self.email_id_source)

        return action(*args, **kwargs)


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

        _, status = self._execute_action(client_id)

        self.assertEqual(status, 403)
        self.auth.domain_for.assert_called_once_with(client_id)

    def test_200(self):
        client_id = str(uuid4())
        email_id = str(uuid4())
        resource_id = str(uuid4())
        domain = 'test.com'
        email = {'_uid': email_id}

        _stored = defaultdict(list)

        def store_objects_mock(upload):
            name, emails = upload
            _stored[name].extend(emails)
            return resource_id

        self.auth.domain_for.return_value = domain
        self.pending_factory.return_value = self.pending_storage
        self.pending_storage.iter.return_value = [email_id]
        self.email_storage.fetch_object.return_value = email
        self.client_storage.store_objects.side_effect = store_objects_mock

        response = self._execute_action(client_id)

        self.assertEqual(response.get('resource_id'), resource_id)
        self.auth.domain_for.assert_called_once_with(client_id)
        self.pending_factory.assert_called_once_with(domain)
        self.pending_storage.iter.assert_called_once_with()
        self.pending_storage.delete.assert_called_once_with(email_id)
        self.email_storage.fetch_object.assert_called_once_with(email_id)
        self.assertEqual(_stored[sync.EMAILS_FILE], [email])

    def _execute_action(self, *args, **kwargs):
        action = actions.DownloadClientEmails(
            auth=self.auth,
            client_storage=self.client_storage,
            email_storage=self.email_storage,
            pending_factory=self.pending_factory)

        return action(*args, **kwargs)


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

        _, status = self._execute_action(client_id, upload_info)

        self.assertEqual(status, 403)
        self.auth.domain_for.assert_called_once_with(client_id)

    def test_200(self):
        client_id = str(uuid4())
        resource_id = str(uuid4())
        domain = 'test.com'
        upload_info = {'resource_id': resource_id}

        self.auth.domain_for.return_value = domain

        _, status = self._execute_action(client_id, upload_info)

        self.assertEqual(status, 200)
        self.auth.domain_for.assert_called_once_with(client_id)
        self.next_task.assert_called_once_with(resource_id)

    def _execute_action(self, *args, **kwargs):
        action = actions.UploadClientEmails(
            auth=self.auth,
            next_task=self.next_task)

        return action(*args, **kwargs)


# noinspection PyTypeChecker
class RegisterClientTests(TestCase):
    def setUp(self):
        self.auth = Mock()
        self.client_storage = Mock()
        self.setup_mailbox = MagicMock()
        self.setup_mx_records = MagicMock()
        self.client_id_source = MagicMock()

    def test_409(self):
        domain = 'test.com'

        self.client_storage.exists.return_value = True

        _, status = self._execute_action({'domain': domain})

        self.assertEqual(status, 409)
        self.client_storage.exists.assert_called_once_with(domain)

    def test_200(self):
        client_id = str(uuid4())
        client_storage_account = 'account'
        client_storage_key = 'key'
        client_storage_container = 'container'
        domain = 'test.com'

        self.client_id_source.return_value = client_id
        self.client_storage.exists.return_value = False
        self.client_storage.access_info.return_value = AccessInfo(
            account=client_storage_account,
            key=client_storage_key,
            container=client_storage_container)

        response = self._execute_action({'domain': domain})

        self.assertEqual(response['client_id'], client_id)
        self.assertEqual(response['storage_account'], client_storage_account)
        self.assertEqual(response['storage_key'], client_storage_key)
        self.assertEqual(response['resource_container'], client_storage_container)
        self.auth.insert.assert_called_once_with(client_id, domain)
        self.assertEqual(self.client_storage.store_objects.call_count, 1)
        self.client_storage.exists.assert_called_once_with(domain)
        self.setup_mailbox.assert_called_once_with(client_id, domain)
        self.setup_mx_records.assert_called_once_with(domain)

    def _execute_action(self, *args, **kwargs):
        action = actions.RegisterClient(
            auth=self.auth,
            client_storage=self.client_storage,
            setup_mailbox=self.setup_mailbox,
            setup_mx_records=self.setup_mx_records,
            client_id_source=self.client_id_source)

        return action(*args, **kwargs)
