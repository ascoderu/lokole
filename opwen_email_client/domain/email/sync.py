from abc import ABCMeta
from abc import abstractmethod
from contextlib import contextmanager
from os import remove
from tarfile import open as tarfile_open
from tempfile import NamedTemporaryFile
from typing import IO
from typing import Iterable
from typing import TypeVar
from uuid import uuid4

from cached_property import cached_property
from libcloud.storage.base import Container
from libcloud.storage.providers import Provider
from libcloud.storage.providers import get_driver
from libcloud.storage.types import ObjectDoesNotExistError

from opwen_email_client.domain.email.client import EmailServerClient
from opwen_email_client.util.serialization import Serializer

T = TypeVar('T')

EXCLUDED_FIELDS = frozenset([
    'read',
])


class Sync(metaclass=ABCMeta):
    @abstractmethod
    def upload(self, items: Iterable[T]) -> Iterable[str]:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def download(self) -> Iterable[T]:
        raise NotImplementedError  # pragma: no cover


class AzureSync(Sync):
    _emails_file = 'emails.jsonl'
    _compression = 'gz'

    def __init__(self, container: str, serializer: Serializer,
                 account_name: str, account_key: str,
                 email_server_client: EmailServerClient,
                 provider: str):

        self._container = container
        self._serializer = serializer
        self._account = account_name
        self._key = account_key
        self._email_server_client = email_server_client
        self._provider = getattr(Provider, provider)

    @cached_property
    def _azure_client(self) -> Container:
        driver = get_driver(self._provider)
        client = driver(self._account, self._key)
        return client.get_container(self._container)

    @classmethod
    @contextmanager
    def _workspace(cls) -> IO:
        temp = NamedTemporaryFile(delete=False)
        try:
            temp.close()
            fobj = open(temp.name, mode=temp.mode)
            try:
                yield fobj
            finally:
                fobj.close()
        finally:
            remove(temp.name)

    @classmethod
    def _open(cls, fileobj, mode, name):
        extension_index = name.rfind('.')
        if extension_index > -1:
            compression = name[extension_index + 1:]
        else:
            compression = cls._compression

        mode = '{}|{}'.format(mode, compression)

        return tarfile_open(fileobj=fileobj, mode=mode)

    def _download_to_stream(self, blobname: str, stream: IO) -> bool:

        try:
            resource = self._azure_client.get_object(blobname)
        except ObjectDoesNotExistError:
            return False
        else:
            for chunk in resource.as_stream():
                stream.write(chunk)
            return True

    def _upload_from_stream(self, blobname: str, stream: IO):
        self._azure_client.upload_object_via_stream(stream, blobname)

    @classmethod
    def _get_file_from_download(cls, archive, name):
        while True:
            member = archive.next()
            if member is None:
                break
            if member.name == name:
                return archive.extractfile(member)
        raise FileNotFoundError(name)

    def download(self):
        resource_id = self._email_server_client.download()
        if not resource_id:
            return

        with self._workspace() as workspace:
            if self._download_to_stream(resource_id, workspace):
                workspace.seek(0)
                with self._open(workspace, 'r', resource_id) as archive:
                    emails = self._get_file_from_download(
                        archive, self._emails_file)
                    for line in emails:
                        yield self._serializer.deserialize(line)

    @classmethod
    def _add_file_to_upload(cls, archive, name, fobj):
        fobj.seek(0)
        archive.add(fobj.name, name)

    def _upload_emails(self, items, archive):
        uploaded_ids = []

        with self._workspace() as uploaded:
            for item in items:
                item = {key: value for (key, value) in item.items()
                        if value is not None
                        and key not in EXCLUDED_FIELDS}
                serialized = self._serializer.serialize(item)
                uploaded.write(serialized)
                uploaded.write(b'\n')
                uploaded_ids.append(item.get('_uid'))

            self._add_file_to_upload(archive, self._emails_file, uploaded)

        return uploaded_ids

    def upload(self, items):
        upload_location = '{}.tar.{}'.format(uuid4(), self._compression)

        with self._workspace() as workspace:
            with self._open(workspace, 'w', upload_location) as archive:
                uploaded_ids = self._upload_emails(items, archive)

            if uploaded_ids:
                workspace.seek(0)
                self._upload_from_stream(upload_location, workspace)
                self._email_server_client.upload(upload_location,
                                                 self._container)

        return uploaded_ids
