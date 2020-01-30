from itertools import count
from mimetypes import guess_type
from time import sleep
from typing import Callable

from cached_property import cached_property
from python_http_client import BadRequestsError
from requests import delete as http_delete
from requests import get as http_get
from requests import post as http_post
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Attachment
from sendgrid.helpers.mail import Content
from sendgrid.helpers.mail import Email
from sendgrid.helpers.mail import Mail
from sendgrid.helpers.mail import MailSettings
from sendgrid.helpers.mail import Personalization
from sendgrid.helpers.mail import SandBoxMode

from opwen_email_server.constants.sendgrid import INBOX_URL
from opwen_email_server.constants.sendgrid import MAILBOX_CREATE_URL
from opwen_email_server.constants.sendgrid import MAILBOX_DETAIL_URL
from opwen_email_server.utils.log import LogMixin
from opwen_email_server.utils.serialization import to_base64


class SendSendgridEmail(LogMixin):
    def __init__(self, key: str, sandbox: bool = False) -> None:
        self._key = key
        self._sandbox = sandbox

    @cached_property
    def _client(self) -> Callable[[Mail], int]:
        if not self._key:

            def send_email_fake(email: Mail) -> int:
                self.log_warning('No key, not sending email %r', email)
                return 202

            return send_email_fake

        client = SendGridAPIClient(api_key=self._key)

        def send_email(email: Mail) -> int:
            if self._sandbox:
                self.log_warning('Sandbox mode, not delivering email %s', email)
                email.mail_settings = MailSettings()
                email.mail_settings.sandbox_mode = SandBoxMode()
                email.mail_settings.sandbox_mode.enable = True

            response = client.send(email.get())
            return response.status_code

        return send_email

    def __call__(self, email: dict) -> bool:
        email_id = email.get('_uid', '')
        email = self._create_email(email, email_id)
        return self._send_email(email, email_id)

    def _send_email(self, email: Mail, email_id: str) -> bool:
        self.log_debug('about to send email %s', email_id)
        try:
            status = self._client(email)
        except BadRequestsError as ex:
            status = ex.status_code
            errors = ex.to_dict.get('errors', [])
            self.log_exception(ex, 'error sending email %s:%s:%r', email_id, email, errors)
        except Exception as ex:
            status = getattr(ex, 'code', -1)
            self.log_exception(ex, 'error sending email %s:%s', email_id, email)
        else:
            self.log_info('sent email %s', email_id)

        return status in (200, 201, 202)

    def _create_email(self, email: dict, email_id: str) -> Mail:
        self.log_debug('converting email %s to sendgrid format', email_id)
        mail = Mail()
        personalization = Personalization()

        for i, to in enumerate(email.get('to', [])):
            personalization.add_to(Email(to))
            self.log_debug('added to %d to email %s', i, email_id)

        for i, cc in enumerate(email.get('cc', [])):
            personalization.add_cc(Email(cc))
            self.log_debug('added cc %d to email %s', i, email_id)

        for i, bcc in enumerate(email.get('bcc', [])):
            personalization.add_bcc(Email(bcc))
            self.log_debug('added bcc %d to email %s', i, email_id)

        mail.add_personalization(personalization)
        self.log_debug('added recipients to email %s', email_id)

        mail.subject = email.get('subject', '(no subject)')
        self.log_debug('added subject to email %s', email_id)

        mail.add_content(Content('text/html', email.get('body', '(no content)')))
        self.log_debug('added content to email %s', email_id)

        mail.from_email = Email(email.get('from'))
        self.log_debug('added from to email %s', email_id)

        for i, attachment in enumerate(email.get('attachments', [])):
            mail.add_attachment(self._create_attachment(attachment))
            self.log_debug('added attachment %d to email %s', i, email_id)

        self.log_debug('converted email %s to sendgrid format', email_id)
        return mail

    @classmethod
    def _create_attachment(cls, attachment: dict) -> Attachment:
        filename = attachment.get('filename', '')
        content = attachment.get('content', b'')

        return Attachment(
            disposition='attachment',
            file_name=filename,
            content_id=filename,
            file_type=guess_type(filename)[0],
            file_content=to_base64(content),
        )


class _SendgridManagement(LogMixin):
    def __init__(self, key: str) -> None:
        self._key = key

    def __call__(self, client_id: str, domain: str) -> None:
        if not self._key:
            self.log_warning('No key, skipping mailbox setup for %s', domain)
            return

        self._run(client_id, domain)

    def _run(self, client_id: str, domain: str) -> None:
        raise NotImplementedError  # pragma: no cover


class DeleteSendgridMailbox(_SendgridManagement):
    def _run(self, client_id: str, domain: str) -> None:
        response = http_delete(
            url=MAILBOX_DETAIL_URL.format(domain),
            headers={
                'Authorization': f'Bearer {self._key}',
            },
        )

        if not response.ok and response.status_code != 404:
            response.raise_for_status()

        self.log_info('Deleted mailbox for %s', domain)


class SetupSendgridMailbox(_SendgridManagement):
    def __init__(self, key: str, max_retries: int, retry_interval_seconds: float):
        super().__init__(key)
        self._max_retries = max_retries
        self._retry_interval_seconds = retry_interval_seconds

    def _run(self, client_id: str, domain: str) -> None:
        for retry in count():
            get_response = http_get(
                url=MAILBOX_DETAIL_URL.format(domain),
                headers={
                    'Authorization': f'Bearer {self._key}',
                },
            )

            if get_response.ok:
                self.log_debug('Mailbox %s already exists', domain)
                break

            create_response = http_post(
                url=MAILBOX_CREATE_URL,
                json={
                    'hostname': domain,
                    'url': INBOX_URL.format(client_id),
                    'spam_check': True,
                    'send_raw': True,
                },
                headers={
                    'Authorization': f'Bearer {self._key}',
                },
            )

            if create_response.ok:
                self.log_info('Set up mailbox for %s', domain)
                break

            if retry > self._max_retries:
                self.log_warning('Too many attempts to set up mailbox for %s', domain)
                create_response.raise_for_status()

            sleep(self._retry_interval_seconds)
