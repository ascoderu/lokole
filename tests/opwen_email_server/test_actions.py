from collections import defaultdict
from copy import deepcopy
from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

from libcloud.storage.types import ObjectDoesNotExistError

from opwen_email_server import actions
from opwen_email_server.constants import sync
from opwen_email_server.services.storage import AccessInfo
from opwen_email_server.utils.serialization import from_jsonl_bytes
from opwen_email_server.utils.serialization import to_jsonl_bytes
from tests.opwen_email_server.helpers import throw


class ActionTests(TestCase):
    @patch.object(actions._Action, '_telemetry_client')
    @patch.object(actions._Action, '_telemetry_channel')
    def test_logs_exception(self, mock_channel, mock_client):
        class TestAction(actions._Action):
            def _action(self):
                int('not-a-number')

        with self.assertRaises(ValueError):
            action = TestAction()
            action()

        mock_client.track_exception.assert_called_once_with()
        mock_channel.flush.assert_called_once_with()


class PingTests(TestCase):
    def test_200(self):
        action = actions.Ping()
        message, status = action()
        self.assertEqual(status, 200)


class SendOutboundEmailsTests(TestCase):
    def setUp(self):
        self.email_storage = Mock()
        self.send_email = MagicMock()

    def test_200(self):
        resource_id = '5f4f519a-f943-421a-94d5-cc9625047e9b'
        email = {'subject': 'test'}

        self.email_storage.fetch_object.return_value = email
        self.send_email.return_value = True

        _, status = self._execute_action(resource_id)

        self.assertEqual(status, 200)
        self.email_storage.fetch_object.assert_called_once_with(resource_id)
        self.send_email.assert_called_once_with(email)

    def test_500(self):
        resource_id = 'b409fbad-ef80-4146-a899-0e229f6627e1'
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
            send_email=self.send_email,
        )

        return action(*args, **kwargs)


class StoreInboundEmailsTests(TestCase):
    def setUp(self):
        self.raw_email_storage = Mock()
        self.email_storage = Mock()
        self.pending_storage = Mock()
        self.email_parser = MagicMock()
        self.next_task = MagicMock()

    def test_202(self):
        resource_id = 'eb93fde9-0cc6-4339-b7d6-f6e838e78f1c'

        self.raw_email_storage.fetch_text.side_effect = throw(ObjectDoesNotExistError(None, None, None))

        _, status = self._execute_action(resource_id)

        self.assertEqual(status, 202)
        self.raw_email_storage.fetch_text.assert_called_once_with(resource_id)
        self.assertFalse(self.raw_email_storage.delete.called)
        self.assertFalse(self.email_storage.store_object.called)
        self.assertFalse(self.pending_storage.store_text.called)
        self.assertFalse(self.email_parser.called)

    def test_200(self):
        resource_id = 'b8dcaf40-fd14-4a89-8898-c9514b0ad724'
        domain = 'test.lokole.ca'
        raw_email = 'dummy-mime'
        parsed_email = {'to': [f'foo@{domain}', 'bar@test.com'], 'sent_at': '2020-02-01 21:17'}
        email_id = '03cbd3b41deca5f92a1d25cc0c50a6eae908d23770fd47ebca0d614eef96a46e'
        stored_email = dict(parsed_email)
        stored_email['_uid'] = email_id

        self.raw_email_storage.fetch_text.return_value = raw_email
        self.email_parser.return_value = parsed_email

        _, status = self._execute_action(resource_id)

        self.assertEqual(status, 200)
        self.raw_email_storage.fetch_text.assert_called_once_with(resource_id)
        self.raw_email_storage.delete.assert_called_once_with(resource_id)
        self.email_storage.store_object.assert_called_once_with(email_id, stored_email)
        self.pending_storage.store_text.assert_called_once_with(f'{domain}/{email_id}', 'pending')
        self.email_parser.assert_called_once_with(raw_email)
        self.next_task.assert_called_once_with(email_id)

    def _execute_action(self, *args, **kwargs):
        action = actions.StoreInboundEmails(
            raw_email_storage=self.raw_email_storage,
            email_storage=self.email_storage,
            pending_storage=self.pending_storage,
            email_parser=self.email_parser,
            next_task=self.next_task,
        )

        return action(*args, **kwargs)


class IndexReceivedEmailForMailboxTests(TestCase):
    def setUp(self):
        self.email_storage = Mock()
        self.mailbox_storage = Mock()

    def test_200(self):
        email_id = '123'
        email = {
            'to': ['1@bar.lokole.ca', 'foo@gmail.com'], 'cc': ['2@baz.lokole.ca'], 'sent_at': '2019-10-26 22:47',
            'from': 'foo@foo'
        }

        self.email_storage.fetch_object.return_value = email

        _, status = self._execute_action(email_id)

        self.assertEqual(status, 200)
        self.email_storage.fetch_object.assert_called_once_with(email_id)
        self.mailbox_storage.store_text.assert_any_call('bar.lokole.ca/1@bar.lokole.ca/received/527869980/123',
                                                        'indexed')
        self.mailbox_storage.store_text.assert_any_call('baz.lokole.ca/2@baz.lokole.ca/received/527869980/123',
                                                        'indexed')
        self.assertEqual(self.mailbox_storage.store_text.call_count, 2)

    def _execute_action(self, *args, **kwargs):
        action = actions.IndexReceivedEmailForMailbox(
            email_storage=self.email_storage,
            mailbox_storage=self.mailbox_storage,
        )

        return action(*args, **kwargs)


class IndexSentEmailForMailboxTests(TestCase):
    def setUp(self):
        self.email_storage = Mock()
        self.mailbox_storage = Mock()

    def test_200(self):
        email_id = '123'
        email = {
            'to': ['1@bar.lokole.ca', 'foo@gmail.com'], 'cc': ['2@baz.lokole.ca'], 'sent_at': '2019-10-26 22:47',
            'from': 'foo@foo.lokole.ca'
        }

        self.email_storage.fetch_object.return_value = email

        _, status = self._execute_action(email_id)

        self.assertEqual(status, 200)
        self.email_storage.fetch_object.assert_called_once_with(email_id)
        self.mailbox_storage.store_text.assert_called_once_with('foo.lokole.ca/foo@foo.lokole.ca/sent/527869980/123',
                                                                'indexed')

    def _execute_action(self, *args, **kwargs):
        action = actions.IndexSentEmailForMailbox(
            email_storage=self.email_storage,
            mailbox_storage=self.mailbox_storage,
        )

        return action(*args, **kwargs)


class StoreWrittenClientEmailsTests(TestCase):
    def setUp(self):
        self.client_storage = Mock()
        self.email_storage = Mock()
        self.user_storage = Mock()
        self.next_task = MagicMock()

    def test_200(self):
        self._test_200(
            attachment_content_bytes=b'some file content',
            attachment_content_base64='c29tZSBmaWxlIGNvbnRlbnQ=',
        )

    def test_200_no_attachments(self):
        self._test_200(
            attachment_content_bytes=None,
            attachment_content_base64=None,
        )

    def _test_200(self, attachment_content_bytes, attachment_content_base64):
        resource_id = 'a2e3d5a7-cb3a-42c3-beeb-d6a2a76089dc'
        email_id = '0194bf59-fb01-479e-bd5e-a59e4b8464d0'
        user_email = 'clemens@developer1.lokole.ca'
        user_password = '$2b$12$9LaXqZMPJi0PiTY.95dIQOvc8LkYQzRlg5a9pDWX47L/npaYqynU2'

        user = {'email': user_email, 'password': user_password}
        client_email = {'from': 'foo@test.com', '_uid': email_id}
        if attachment_content_base64:
            client_email['attachments'] = [{'filename': 'test.txt', 'content': attachment_content_base64}]

        server_email = deepcopy(client_email)
        if attachment_content_bytes:
            server_email['attachments'][0]['content'] = attachment_content_bytes

        self.client_storage.fetch_objects.side_effect = [[client_email], [user]]

        _, status = self._execute_action(resource_id)

        self.assertEqual(status, 200)
        self.client_storage.fetch_objects.assert_any_call(resource_id, (sync.EMAILS_FILE, from_jsonl_bytes))
        self.email_storage.store_object.assert_called_once_with(email_id, server_email)
        self.next_task.assert_called_once_with(email_id)
        self.client_storage.fetch_objects.assert_any_call(resource_id, (sync.USERS_FILE, from_jsonl_bytes))
        self.user_storage.store_object.assert_called_once_with(f'developer1.lokole.ca/{user_email}', user)
        self.client_storage.delete.assert_called_once_with(resource_id)

    def _execute_action(self, *args, **kwargs):
        action = actions.StoreWrittenClientEmails(
            client_storage=self.client_storage,
            email_storage=self.email_storage,
            user_storage=self.user_storage,
            next_task=self.next_task,
        )

        return action(*args, **kwargs)


class ReceiveInboundEmailTests(TestCase):
    def setUp(self):
        self.auth = Mock()
        self.raw_email_storage = Mock()
        self.next_task = MagicMock()
        self.email_id_source = MagicMock()

    def test_403(self):
        client_id = '4f7accdf-f387-46e9-bdf1-f227ffdb724d'
        domain = None
        email = 'dummy-mime'

        self.auth.domain_for.return_value = domain

        _, status = self._execute_action(client_id, email)

        self.assertEqual(status, 403)
        self.auth.domain_for.assert_called_once_with(client_id)

    def test_200(self):
        client_id = 'e440953a-4226-47a3-a116-2698c667b153'
        email_id = 'dfbab492b9adcf20ca8424b993b0f7ec26731d069be4d451ebbf7910937a999c'
        domain = 'test.com'
        email = 'dummy-mime'

        self.auth.domain_for.return_value = domain

        _, status = self._execute_action(client_id, email)

        self.assertEqual(status, 200)
        self.auth.domain_for.assert_called_once_with(client_id)
        self.raw_email_storage.store_text.assert_called_once_with(email_id, email)
        self.next_task.assert_called_once_with(email_id)

    def test_is_idempotent(self):
        client_id = '8c753257-6b75-4a26-a81b-bb9c09d38b52'
        domain = 'test.com'
        email = 'dummy-mime'
        num_repeated_emails = 3

        self.auth.domain_for.return_value = domain

        for _ in range(num_repeated_emails):
            _, status = self._execute_action(client_id, email)
            self.assertEqual(status, 200)

        self.assertHasSameCalls(self.raw_email_storage.store_text, num_repeated_emails)
        self.assertHasSameCalls(self.next_task, num_repeated_emails)

    def assertHasSameCalls(self, mocked_function, num_calls):
        self.assertEqual(len(mocked_function.call_args_list), num_calls)
        for call in mocked_function.call_args_list:
            self.assertEqual(call, mocked_function.call_args_list[0])

    def _execute_action(self, *args, **kwargs):
        action = actions.ReceiveInboundEmail(
            auth=self.auth,
            raw_email_storage=self.raw_email_storage,
            next_task=self.next_task,
        )

        return action(*args, **kwargs)


class ProcessServiceEmailTests(TestCase):
    def setUp(self):
        self.raw_email_storage = Mock()
        self.email_storage = Mock()
        self.next_task = MagicMock()
        self.registry = {'service@lokole.ca': (lambda email: email)}
        self.email_parser = MagicMock()

    def test_202(self):
        resource_id = 'eb93fde9-0cc6-4339-b7d6-f6e838e78f1c'
        self.raw_email_storage.fetch_text.side_effect = throw(ObjectDoesNotExistError(None, None, None))

        _, status = self._execute_action(resource_id)
        self.assertEqual(status, 202)

    def test_200(self):
        resource_id = 'eb93fde9-0cc6-4339-b7d6-f6e838e78f1c'
        email = 'some-mime'
        parsed_email = {
            'to': ['service@lokole.ca', 'foo@test.com'], 'from': 'user@lokole.ca', 'sent_at': '2020-02-01 21:17'
        }
        self.raw_email_storage.return_value = email
        self.email_parser.return_value = parsed_email

        _, status = self._execute_action(resource_id)
        self.assertEqual(status, 200)
        self.email_storage.store_object.assert_called_once()
        self.next_task.assert_called_once()

    def _execute_action(self, *args, **kwargs):
        action = actions.ProcessServiceEmail(
            raw_email_storage=self.raw_email_storage,
            email_storage=self.email_storage,
            next_task=self.next_task,
            registry=self.registry,
            email_parser=self.email_parser,
        )

        return action(*args, **kwargs)


class DownloadClientEmailsTests(TestCase):
    def setUp(self):
        self.auth = Mock()
        self.client_storage = Mock()
        self.email_storage = Mock()
        self.pending_storage = Mock()

    def test_400(self):
        client_id = 'af962175-8757-4ac4-a199-2387b06379fa'
        domain = 'test.com'

        self.auth.domain_for.return_value = domain
        self.client_storage.compression_formats.return_value = ['gz']

        _, status = self._execute_action(client_id, 'xyz')

        self.assertEqual(status, 400)

    def test_403(self):
        client_id = '8bb3c924-aee6-4934-99dd-c7e50689489d'
        domain = None

        self.auth.domain_for.return_value = domain

        _, status = self._execute_action(client_id, 'gz')

        self.assertEqual(status, 403)

    def test_200(self):
        self._test_200(
            attachment_content_bytes=b'some file content',
            attachment_content_base64='c29tZSBmaWxlIGNvbnRlbnQ=',
        )

    def test_200_no_attachments(self):
        self._test_200(
            attachment_content_bytes=None,
            attachment_content_base64=None,
        )

    def _test_200(self, attachment_content_bytes, attachment_content_base64):
        client_id = 'f4e2cdc6-c79c-44ad-af35-071f8ea6e176'
        email_id = 'b69bee6b-72fb-4b7f-a2ad-9aa7e375cf18'
        resource_id = 'ffc86666-a9c6-403d-8a9c-c334465657c2'
        domain = 'test.com'

        server_email = {'_uid': email_id}
        if attachment_content_bytes:
            server_email['attachments'] = [{'filename': 'test.txt', 'content': attachment_content_bytes}]

        client_email = deepcopy(server_email)
        if attachment_content_base64:
            client_email['attachments'][0]['content'] = attachment_content_base64

        _stored = defaultdict(list)
        _compression = defaultdict(list)
        _serializers = defaultdict(list)

        def store_objects_mock(upload, compression):
            name, emails, serializer = upload
            _stored[name].extend(emails)
            _compression[name].append(compression)
            _serializers[name].append(serializer)
            return resource_id

        self.auth.domain_for.return_value = domain
        self.pending_storage.iter.return_value = [email_id]
        self.email_storage.fetch_object.return_value = server_email
        self.client_storage.store_objects.side_effect = store_objects_mock
        self.client_storage.compression_formats.return_value = ['gz']

        response = self._execute_action(client_id, 'gz')

        self.assertEqual(response.get('resource_id'), resource_id)
        self.auth.domain_for.assert_called_once_with(client_id)
        self.pending_storage.iter.assert_called_once_with(f'{domain}/')
        self.pending_storage.delete.assert_called_once_with(f'{domain}/{email_id}')
        self.email_storage.fetch_object.assert_called_once_with(email_id)
        self.assertEqual(_stored[sync.EMAILS_FILE], [client_email])
        self.assertEqual(_compression[sync.EMAILS_FILE], ['gz'])
        self.assertEqual(_serializers[sync.EMAILS_FILE], [to_jsonl_bytes])

    def _execute_action(self, *args, **kwargs):
        action = actions.DownloadClientEmails(
            auth=self.auth,
            client_storage=self.client_storage,
            email_storage=self.email_storage,
            pending_storage=self.pending_storage,
        )

        return action(*args, **kwargs)


class UploadClientEmailsTests(TestCase):
    def setUp(self):
        self.auth = Mock()
        self.next_task = MagicMock()

    def test_403(self):
        client_id = 'e7f1c2c9-fa45-4f63-a965-a3dcddb68420'
        domain = None
        upload_info = {}

        self.auth.domain_for.return_value = domain

        _, status = self._execute_action(client_id, upload_info)

        self.assertEqual(status, 403)
        self.auth.domain_for.assert_called_once_with(client_id)

    def test_200(self):
        client_id = 'ef54b4bb-0f48-4dd3-8e3d-896261a15a8c'
        resource_id = '433953ac-9be7-4525-a64c-3d25926d10ca'
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
            next_task=self.next_task,
        )

        return action(*args, **kwargs)


class RegisterClientTests(TestCase):
    def setUp(self):
        self.auth = Mock()
        self.client_storage = Mock()
        self.setup_mailbox = MagicMock()
        self.setup_mx_records = MagicMock()
        self.client_id_source = MagicMock()

    def test_200(self):
        client_id = '187ba644-4d46-49f6-a634-017d7f58e338'
        client_storage_account = 'account'
        client_storage_key = 'key'
        client_storage_container = 'container'
        domain = 'test.com'
        user = 'user'

        self.client_id_source.return_value = client_id
        self.client_storage.access_info.return_value = AccessInfo(
            account=client_storage_account,
            key=client_storage_key,
            container=client_storage_container,
        )

        _, status = self._execute_action(domain, user)

        self.assertEqual(status, 200)
        self.client_id_source.assert_called_once_with()
        self.auth.insert.assert_called_with(client_id, domain, user)
        self.assertEqual(self.client_storage.ensure_exists.call_count, 1)
        self.setup_mailbox.assert_called_once_with(client_id, domain)
        self.setup_mx_records.assert_called_once_with(domain)

    def _execute_action(self, *args, **kwargs):
        action = actions.RegisterClient(
            auth=self.auth,
            client_storage=self.client_storage,
            setup_mailbox=self.setup_mailbox,
            setup_mx_records=self.setup_mx_records,
            client_id_source=self.client_id_source,
        )

        return action(*args, **kwargs)


class CreateClientTests(TestCase):
    def setUp(self):
        self.auth = Mock()
        self.task = MagicMock()

    def test_400(self):
        domain = 'TEST.com'
        user = 'user'

        _, status = self._execute_action({'domain': domain}, user=user)

        self.assertEqual(status, 400)

    def test_409(self):
        domain = 'test.com'
        user = 'user'

        self.auth.client_id_for.return_value = '123'

        _, status = self._execute_action({'domain': domain}, user=user)

        self.assertEqual(status, 409)
        self.auth.client_id_for.assert_called_once_with(domain)

    def test_200(self):
        domain = 'test.com'
        user = 'user'

        self.auth.client_id_for.return_value = None

        _, status = self._execute_action({'domain': domain}, user=user)

        self.assertEqual(status, 201)
        self.auth.client_id_for.assert_called_once_with(domain)
        self.task.assert_called_once_with(domain, user)

    def _execute_action(self, *args, **kwargs):
        action = actions.CreateClient(
            auth=self.auth,
            task=self.task,
        )

        return action(*args, **kwargs)


class ListClientsTests(TestCase):
    def setUp(self):
        self.auth = Mock()

    def test_200(self):
        domains = ['1.test.com', '2.test.com']

        self.auth.domains.return_value = domains

        response = self._execute_action()

        self.assertEqual(response['clients'], [{'domain': '1.test.com'}, {'domain': '2.test.com'}])
        self.auth.domains.assert_called_once()

    def _execute_action(self, *args, **kwargs):
        action = actions.ListClients(auth=self.auth)

        return action(*args, **kwargs)


class GetClientTests(TestCase):
    def setUp(self):
        self.auth = Mock()
        self.client_storage = Mock()
        self.setup_mailbox = MagicMock()
        self.setup_mx_records = MagicMock()
        self.client_id_source = MagicMock()

    def test_400(self):
        domain = 'TEST.com'
        user = 'user'

        _, status = self._execute_action(domain, user=user)

        self.assertEqual(status, 400)

    def test_404(self):
        domain = 'test.com'
        user = 'user'

        self.auth.client_id_for.return_value = None

        _, status = self._execute_action(domain, user=user)

        self.assertEqual(status, 404)
        self.auth.client_id_for.assert_called_once_with(domain)

    def test_403(self):
        domain = 'test.com'
        user = 'user'
        client_id = '187ba644-4d46-49f6-a634-017d7f58e338'

        self.auth.client_id_for.return_value = client_id
        self.auth.is_owner.return_value = False

        _, status = self._execute_action(domain, user=user)

        self.assertEqual(status, 403)

    def test_200(self):
        client_id = '187ba644-4d46-49f6-a634-017d7f58e338'
        client_storage_account = 'account'
        client_storage_key = 'key'
        client_storage_container = 'container'
        domain = 'test.com'
        user = 'user'

        self.auth.client_id_for.return_value = client_id
        self.client_storage.access_info.return_value = AccessInfo(
            account=client_storage_account,
            key=client_storage_key,
            container=client_storage_container,
        )

        response = self._execute_action(domain, user=user)

        self.assertEqual(response['client_id'], client_id)
        self.assertEqual(response['storage_account'], client_storage_account)
        self.assertEqual(response['storage_key'], client_storage_key)
        self.assertEqual(response['resource_container'], client_storage_container)
        self.auth.client_id_for.assert_called_once_with(domain)

    def _execute_action(self, *args, **kwargs):
        action = actions.GetClient(
            auth=self.auth,
            client_storage=self.client_storage,
        )

        return action(*args, **kwargs)


class DeleteClientTests(TestCase):
    def setUp(self):
        self.auth = Mock()
        self.delete_mailbox = MagicMock()
        self.delete_mx_records = MagicMock()
        self.mailbox_storage = Mock()
        self.pending_storage = Mock()
        self.user_storage = Mock()

    def test_400(self):
        domain = 'TEST.com'
        user = 'user'

        _, status = self._execute_action(domain, user=user)

        self.assertEqual(status, 400)

    def test_404(self):
        domain = 'test.com'
        user = 'user'

        self.auth.client_id_for.return_value = None

        _, status = self._execute_action(domain, user=user)

        self.assertEqual(status, 404)
        self.auth.client_id_for.assert_called_once_with(domain)

    def test_403(self):
        domain = 'test.com'
        user = 'user'
        client_id = '187ba644-4d46-49f6-a634-017d7f58e338'

        self.auth.client_id_for.return_value = client_id
        self.auth.is_owner.return_value = False

        _, status = self._execute_action(domain, user=user)

        self.assertEqual(status, 403)
        self.auth.client_id_for.assert_called_once_with(domain)
        self.auth.is_owner.assert_called_once_with(domain, user)

    def test_200(self):
        client_id = '187ba644-4d46-49f6-a634-017d7f58e338'
        domain = 'test.com'
        user = 'user'

        self.auth.client_id_for.return_value = client_id
        self.auth.is_owner.return_value = True
        self.mailbox_storage.iter.return_value = ['1/2/a', '1/2/b']
        self.pending_storage.iter.return_value = ['c', 'd', 'e']
        self.user_storage.iter.return_value = [f'{user}@{domain}']

        _, status = self._execute_action(domain, user=user)

        self.assertEqual(status, 200)
        self.auth.client_id_for.assert_called_once_with(domain)
        self.auth.is_owner.assert_called_once_with(domain, user)
        self.auth.delete.assert_called_once_with(client_id, domain)
        self.delete_mailbox.assert_called_once_with(client_id, domain)
        self.delete_mx_records.assert_called_once_with(domain)
        self.mailbox_storage.iter.assert_called_once_with(f'{domain}/')
        self.mailbox_storage.delete.assert_any_call(f'{domain}/1/2/a')
        self.mailbox_storage.delete.assert_any_call(f'{domain}/1/2/b')
        self.assertEqual(self.mailbox_storage.delete.call_count, 2)
        self.pending_storage.iter.assert_called_once_with(f'{domain}/')
        self.pending_storage.delete.assert_any_call(f'{domain}/c')
        self.pending_storage.delete.assert_any_call(f'{domain}/d')
        self.pending_storage.delete.assert_any_call(f'{domain}/e')
        self.assertEqual(self.pending_storage.delete.call_count, 3)
        self.user_storage.iter.assert_called_once_with(f'{domain}/')
        self.user_storage.delete.assert_called_once_with(f'{domain}/{user}@{domain}')

    def _execute_action(self, *args, **kwargs):
        action = actions.DeleteClient(
            auth=self.auth,
            delete_mailbox=self.delete_mailbox,
            delete_mx_records=self.delete_mx_records,
            mailbox_storage=self.mailbox_storage,
            pending_storage=self.pending_storage,
            user_storage=self.user_storage,
        )

        return action(*args, **kwargs)


class CalculateNumberOfUsersMetricTests(TestCase):
    def setUp(self):
        self.auth = Mock()
        self.user_storage = Mock()

    def test_403(self):
        domain = 'test.com'
        user = 'user'

        self.auth.is_owner.return_value = False

        _, status = self._execute_action(domain, user=user)

        self.assertEqual(status, 403)

    def test_200(self):
        domain = 'test.com'
        user = 'user'
        users = [
            'test.com/user1',
            'test.com/user2',
            'test.com/user3',
        ]

        self.auth.is_owner.return_value = True
        self.user_storage.iter.return_value = users

        response = self._execute_action(domain, user=user)

        self.assertEqual(response['users'], len(users))
        self.auth.is_owner.assert_called_once_with(domain, user)
        self.user_storage.iter.assert_called_once_with(f'{domain}/')

    def _execute_action(self, *args, **kwargs):
        action = actions.CalculateNumberOfUsersMetric(
            auth=self.auth,
            user_storage=self.user_storage,
        )

        return action(*args, **kwargs)


class CalculatePendingEmailsMetricTests(TestCase):
    def setUp(self):
        self.auth = Mock()
        self.pending_storage = Mock()

    def test_403(self):
        domain = 'test.com'
        user = 'user'

        self.auth.is_owner.return_value = False

        _, status = self._execute_action(domain, user=user)

        self.assertEqual(status, 403)

    def test_200(self):
        domain = 'test.com'
        user = 'user'
        pending_email_ids = [
            '1de2ceb6-4f82-4cad-86ac-815bcbcb801c',
            '9eb3f071-0f95-4317-befa-060c05ba3632',
            '1e79ad99-1778-47b0-a2db-3c3be404640d',
        ]

        self.auth.is_owner.return_value = True
        self.pending_storage.iter.return_value = pending_email_ids

        response = self._execute_action(domain, user=user)

        self.assertEqual(response['pending_emails'], len(pending_email_ids))
        self.auth.is_owner.assert_called_once_with(domain, user)
        self.pending_storage.iter.assert_called_once_with(f'{domain}/')

    def _execute_action(self, *args, **kwargs):
        action = actions.CalculatePendingEmailsMetric(
            auth=self.auth,
            pending_storage=self.pending_storage,
        )

        return action(*args, **kwargs)
