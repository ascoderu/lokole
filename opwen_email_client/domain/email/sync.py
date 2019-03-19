from abc import ABCMeta
from abc import abstractmethod
from collections import namedtuple
from contextlib import contextmanager
from os import remove
from tarfile import TarFile
from tempfile import NamedTemporaryFile
from typing import IO
from typing import Iterable
from typing import Tuple
from typing import TypeVar
from uuid import uuid4

from cached_property import cached_property
from libcloud.storage.base import Container
from libcloud.storage.providers import Provider
from libcloud.storage.providers import get_driver
from libcloud.storage.types import ObjectDoesNotExistError
from xtarfile import open as tarfile_open

from opwen_email_client.domain.email.client import EmailServerClient
from opwen_email_client.util.serialization import Serializer

T = TypeVar('T')

Download = namedtuple('Download', ('name', 'optional', 'type_'))


class Sync(metaclass=ABCMeta):
    @abstractmethod
    def upload(self, items: Iterable[T]) -> Iterable[str]:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def download(self) -> Iterable[T]:
        raise NotImplementedError  # pragma: no cover


class AzureSync(Sync):
    _emails_file = 'emails.jsonl'
    _attachments_file = 'zattachments.jsonl'

    _download_files = (
        Download(name=_emails_file, optional=False, type_='email'),
        Download(name=_attachments_file, optional=True, type_='attachment'),
    )

    def __init__(self, container: str, serializer: Serializer,
                 account_name: str, account_key: str,
                 email_server_client: EmailServerClient,
                 provider: str, compression: str):

        self._container = container
        self._serializer = serializer
        self._account = account_name
        self._key = account_key
        self._email_server_client = email_server_client
        self._provider = getattr(Provider, provider)
        self._compression = compression

    @cached_property
    def _azure_client(self) -> Container:
        driver = get_driver(self._provider)
        client = driver(self._account, self._key)
        return client.get_container(self._container)

    @classmethod
    @contextmanager
    def _workspace(cls, suffix: str) -> IO:
        temp = NamedTemporaryFile(suffix=suffix, delete=False)
        try:
            temp.close()
            fobj = open(temp.name, mode=temp.mode)
            try:
                yield fobj
            finally:
                fobj.close()
        finally:
            remove(temp.name)

    def _open(self, path: str, mode: str) -> TarFile:
        extension_index = path.rfind('.')
        if extension_index > -1:
            compression = path[extension_index + 1:]
        else:
            compression = self._compression

        mode = '{}|{}'.format(mode, compression)

        return tarfile_open(path, mode=mode)

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
    def _get_file_from_download(cls, archive, downloads: Iterable[Download]) \
            -> Iterable[Tuple[Download, IO[bytes]]]:

        downloads = {download.name: download for download in downloads}

        while True:
            member = archive.next()
            if member is None:
                break

            filename = member.name
            try:
                download = downloads[filename]
            except KeyError:
                pass
            else:
                yield download, archive.extractfile(member)
                del downloads[filename]

        missing_downloads = [
            filename for filename, download in downloads.items()
            if not download.optional
        ]

        if missing_downloads:
            raise FileNotFoundError(','.join(missing_downloads))

    def download(self):
        resource_id = self._email_server_client.download()
        if not resource_id:
            return

        with self._workspace(resource_id) as workspace:
            if not self._download_to_stream(resource_id, workspace):
                return

            workspace.seek(0)
            with self._open(workspace.name, 'r') as archive:
                for download, fobj in self._get_file_from_download(
                        archive, self._download_files):
                    for line in fobj:
                        obj = self._serializer.deserialize(
                            line, download.type_)
                        obj['_type'] = download.type_
                        yield obj

    def _upload_emails(self, items, archive):
        uploaded_ids = []

        with self._workspace(self._emails_file) as uploaded:
            for item in items:
                item = {key: value for (key, value) in item.items()
                        if value is not None}
                item.pop('read', False)
                for attachment in item.get('attachments', []):
                    attachment.pop('_uid', '')
                serialized = self._serializer.serialize(item)
                uploaded.write(serialized)
                uploaded.write(b'\n')
                uploaded_ids.append(item.get('_uid'))

            uploaded.seek(0)
            archive.add(uploaded.name, self._emails_file)

        return uploaded_ids

    def upload(self, items):
        upload_location = '{}.tar.{}'.format(uuid4(), self._compression)

        with self._workspace(upload_location) as workspace:
            with self._open(workspace.name, 'w') as archive:
                uploaded_ids = self._upload_emails(items, archive)

            if uploaded_ids:
                workspace.seek(0)
                self._upload_from_stream(upload_location, workspace)
                self._email_server_client.upload(upload_location,
                                                 self._container)

        return uploaded_ids
