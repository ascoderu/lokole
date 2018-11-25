from collections import namedtuple
from gzip import open as gzip_open
from io import BytesIO
from typing import Iterable
from typing import Iterator
from typing import Optional
from uuid import uuid4

from cached_property import cached_property
from libcloud.storage.base import Container
from libcloud.storage.base import StorageDriver  # noqa
from libcloud.storage.providers import get_driver
from libcloud.storage.types import ContainerDoesNotExistError
from libcloud.storage.types import ObjectDoesNotExistError
from libcloud.storage.types import Provider

from opwen_email_server.utils.log import LogMixin
from opwen_email_server.utils.serialization import from_json
from opwen_email_server.utils.serialization import gunzip_string
from opwen_email_server.utils.serialization import gzip_string
from opwen_email_server.utils.serialization import to_json
from opwen_email_server.utils.temporary import create_tempfilename
from opwen_email_server.utils.temporary import removing

AccessInfo = namedtuple('AccessInfo', ['account', 'key', 'container'])


class _BaseAzureStorage(LogMixin):
    def __init__(self, account: str, key: str, container: str,
                 provider: str) -> None:
        self._account = account
        self._key = key
        self._container = container
        self._provider = getattr(Provider, provider)

    @cached_property
    def _client(self) -> Container:
        driver = get_driver(self._provider)
        client = driver(self._account, self._key)  # type: StorageDriver
        try:
            container = client.get_container(self._container)
        except ContainerDoesNotExistError:
            container = client.create_container(self._container)
        return container

    def access_info(self) -> AccessInfo:
        return AccessInfo(
            account=self._account,
            key=self._key,
            container=self._container)

    def extra_log_args(self):
        yield 'container %s', self._container

    def delete(self, resource_id: str):
        resource = self._client.get_object(resource_id)
        resource.delete()

    def iter(self) -> Iterator[str]:
        for resource in self._client.list_objects():
            yield resource.name


class AzureFileStorage(_BaseAzureStorage):
    def store_file(self, resource_id: str, path: str):
        self.log_debug('storing file %s at %s', path, resource_id)
        self._client.upload_object(path, resource_id)

    def fetch_file(self, resource_id: str) -> str:
        resource = self._client.get_object(resource_id)
        path = create_tempfilename()
        resource.download(path)
        self.log_debug('fetched file %s from %s', path, resource_id)
        return path


class AzureTextStorage(_BaseAzureStorage):
    def store_text(self, resource_id: str, text: str):
        self.log_debug('storing %d characters at %s', len(text), resource_id)
        upload = BytesIO()
        upload.write(gzip_string(text))
        upload.seek(0)
        self._client.upload_object_via_stream(upload, resource_id)

    def fetch_text(self, resource_id: str) -> str:
        download = BytesIO()
        resource = self._client.get_object(resource_id)
        for chunk in resource.as_stream():
            download.write(chunk)
        download.seek(0)
        text = gunzip_string(download.read())
        self.log_debug('fetched %d characters from %s', len(text), resource_id)
        return text


class AzureObjectsStorage(LogMixin):
    _encoding = 'utf-8'

    def __init__(self, file_storage: AzureFileStorage) -> None:
        self._file_storage = file_storage

    def access_info(self) -> AccessInfo:
        return self._file_storage.access_info()

    def store_objects(self, objs: Iterable[dict],
                      resource_id: Optional[str] = None) -> Optional[str]:

        resource_id = resource_id or str(uuid4())

        num_stored = 0
        with removing(create_tempfilename()) as path:
            with gzip_open(path, 'wb') as fobj:
                for obj in objs:
                    serialized = to_json(obj)
                    encoded = serialized.encode(self._encoding)
                    fobj.write(encoded)
                    fobj.write(b'\n')
                    num_stored += 1
                    self.log_debug('stored object %s', obj.get('_uid', ''))

            if num_stored > 0:
                self._file_storage.store_file(resource_id, path)

        self.log_debug('stored %d objects at %s', num_stored, resource_id)
        return resource_id if num_stored > 0 else None

    def _parse_jsonl(self, line: str) -> Optional[dict]:
        serialized = line.strip()

        if not serialized.startswith('{'):
            self.log_debug('Skipping non-JSONL line %s', line)
            return None

        if serialized[-1] != '}' and serialized[-1] != ',':
            self.log_debug('Skipping non-JSONL line %s', line)
            return None

        if serialized.endswith(','):
            serialized = serialized[:len(serialized) - 1]

        try:
            return from_json(serialized)
        except ValueError:
            self.log_debug('Skipping non-JSONL line %s', line)
            return None

    def fetch_objects(self, resource_id: str) -> Iterable[dict]:
        num_fetched = 0
        with removing(self._file_storage.fetch_file(resource_id)) as path:
            with gzip_open(path, 'rb') as fobj:
                for encoded in fobj:
                    serialized = encoded.decode(self._encoding)
                    obj = self._parse_jsonl(serialized)
                    if not obj:
                        continue
                    num_fetched += 1
                    self.log_debug('fetched email %s', obj.get('_uid'))
                    yield obj
        self.log_debug('fetched %d objects from %s', num_fetched, resource_id)

    def exists(self, resource_id: str) -> bool:
        try:
            self._file_storage.fetch_file(resource_id)
        except ObjectDoesNotExistError:
            return False
        else:
            return True

    def delete(self, resource_id: str):
        self._file_storage.delete(resource_id)


class AzureObjectStorage(LogMixin):
    def __init__(self, text_storage: AzureTextStorage):
        self._text_storage = text_storage

    def fetch_object(self, resource_id: str) -> dict:
        serialized = self._text_storage.fetch_text(resource_id)
        return from_json(serialized)

    def store_object(self, resource_id: str, obj: dict) -> None:
        serialized = to_json(obj)
        self._text_storage.store_text(resource_id, serialized)
