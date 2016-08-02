from datetime import datetime
from os import makedirs
from os import path
from shutil import copy

from opwen_webapp.models import Email
from opwen_webapp.models import User
from utils.temporary import create_temporary_directory


class Serializer(object):
    _date_format = '%Y-%m-%d %H:%M'

    _account_name_field = 'name'
    _account_email_field = 'email'

    _email_date_field = 'date'
    _email_to_field = 'to'
    _email_sender_field = 'from'
    _email_subject_field = 'subject'
    _email_body_field = 'message'
    _email_attachments_field = 'attachments'
    _email_attachment_name_field = 'filename'
    _email_attachment_path_field = 'relativepath'

    def __init__(self, fileformatter=None, compressor=None, app=None):
        """
        :type fileformatter: (str, str) -> utils.fileformatter.FileFormatter
        :type compressor: () -> utils.compressor.DirectoryCompressor
        :type app: flask.Flask

        """
        self.fileformatter = fileformatter
        self.compressor = compressor()
        self.accounts_filename = None
        self.emails_filename = None
        self.attachments_directoryname = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        :type app: flask.Flask

        """
        self.accounts_filename = app.config.get('REMOTE_SERIALIZER_ACCOUNTS_NAME')
        self.emails_filename = app.config.get('REMOTE_SERIALIZER_EMAILS_NAME')
        self.attachments_directoryname = app.config.get('REMOTE_SERIALIZER_ATTACHMENTS_NAME')
        app.serializer = self

    def _serialize_account(self, account, fobj):
        """
        :type account: opwen_webapp.models.User

        """
        fobj.write({
            self._account_name_field: account.name,
            self._account_email_field: account.email,
        })

    def _serialize_accounts(self, accounts, workspace):
        """
        :type accounts: collections.Iterable[User]
        :type workspace: str

        """
        if not accounts:
            return

        accounts_path = path.join(workspace, self.accounts_filename)
        with self.fileformatter(accounts_path, 'w') as manifest:
            for account in accounts:
                self._serialize_account(account, manifest)

    def _format_date(self, date):
        """
        :type date: datetime
        :rtype: str

        """
        return date.strftime(self._date_format) if date else None

    def _parse_date(self, date):
        """
        :type date: str
        :rtype: datetime

        """
        return datetime.strptime(date, self._date_format) if date else None

    def _serialize_email(self, email, fobj):
        """
        :type email: Email

        """
        fobj.write({
            self._email_date_field: self._format_date(email.date),
            self._email_to_field: email.to,
            self._email_sender_field: email.sender,
            self._email_subject_field: email.subject,
            self._email_body_field: email.body,
            self._email_attachments_field: [{
                self._email_attachment_name_field: attachment.name,
                self._email_attachment_path_field: path.join(
                    self.attachments_directoryname,
                    path.basename(attachment.path)),
            } for attachment in email.attachments],
        })

    def _serialize_attachments(self, attachments, workspace):
        """
        :type attachments: collections.Iterable[opwen_webapp.models.Attachment]
        :type workspace: str

        """
        if not attachments:
            return

        target_directory = path.join(workspace, self.attachments_directoryname)
        makedirs(target_directory, mode=0o700, exist_ok=True)
        for attachment in attachments:
            copy(attachment.path, target_directory)

    def _serialize_emails(self, emails, workspace):
        """
        :type emails: collections.Iterable[Email]
        :type workspace: str

        """
        if not emails:
            return

        emails_path = path.join(workspace, self.emails_filename)
        with self.fileformatter(emails_path, 'w') as manifest:
            for email in emails:
                self._serialize_email(email, manifest)
                self._serialize_attachments(email.attachments, workspace)

    def serialize(self, emails=None, accounts=None):
        """
        :type emails: collections.Iterable[Email]
        :type accounts: collections.Iterable[User]
        :rtype: str

        """
        if not emails and not accounts:
            return None

        with create_temporary_directory() as workspace:
            self._serialize_emails(emails, workspace)
            self._serialize_accounts(accounts, workspace)
            serialized = self.compressor.compress(workspace)
        return serialized

    def _deserialize_attachments(self, serialized, archive, workspace):
        """
        :type serialized: dict
        :type archive: str
        :type workspace: str
        :rtype: collections.Iterable[(str,str)]

        """
        attachments = serialized.get(self._email_attachments_field, [])
        for attachment in attachments:
            attachment_name = attachment.get(self._email_attachment_name_field)
            attachment_path = attachment.get(self._email_attachment_path_field)
            attachment_path = self.compressor.decompress(
                archive, attachment_path, workspace)
            yield attachment_path, attachment_name

    def _deserialize_email(self, serialized, archive, workspace):
        """
        :type serialized: dict
        :type archive: str
        :type workspace: str
        :rtype: Email

        """
        attached = self._deserialize_attachments(serialized, archive, workspace)
        return Email(
            date=self._parse_date(serialized.get(self._email_date_field)),
            to=serialized.get(self._email_to_field),
            sender=serialized.get(self._email_sender_field),
            subject=serialized.get(self._email_subject_field),
            body=serialized.get(self._email_body_field),
            attachments=list(attached))

    def _deserialize_emails(self, archive, workspace):
        """
        :type archive: str
        :type workspace: str
        :rtype: collections.Iterable[Email]

        """
        emails_path = self.compressor.decompress(
            archive, self.emails_filename, workspace)
        with self.fileformatter(emails_path, 'r') as manifest:
            for item in manifest:
                yield self._deserialize_email(item, archive, workspace)

    def _deserialize_account(self, serialized):
        """
        :type serialized: dict
        :rtype: User

        """
        return User(name=serialized.get(self._account_name_field),
                    email=serialized.get(self._account_email_field))

    def _deserialize_accounts(self, archive, workspace):
        """
        :type archive: str
        :type workspace: str
        :rtype: collections.Iterable[User]

        """
        accounts_path = self.compressor.decompress(
            archive, self.accounts_filename, workspace)
        with self.fileformatter(accounts_path, 'r') as manifest:
            for item in manifest:
                yield self._deserialize_account(item)

    def deserialize(self, serialized):
        """
        :type serialized: str
        :rtype: (list[Email], list[User])

        """
        if not serialized or not path.isfile(serialized):
            return [], []

        with create_temporary_directory() as workspace:
            emails = self._deserialize_emails(serialized, workspace)
            accounts = self._deserialize_accounts(serialized, workspace)

            try:
                emails = list(emails)
            except ValueError:
                emails = []
            try:
                accounts = list(accounts)
            except ValueError:
                accounts = []

        return emails, accounts
