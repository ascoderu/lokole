from collections import namedtuple
from io import BytesIO
from tarfile import TarFile
from tempfile import NamedTemporaryFile
from typing import IO
from typing import Callable
from typing import Iterable
from typing import Iterator
from typing import Optional
from typing import Tuple

from cached_property import cached_property
from libcloud.storage.base import Container
from libcloud.storage.base import Object
from libcloud.storage.base import StorageDriver
from libcloud.storage.providers import get_driver
from libcloud.storage.types import ContainerAlreadyExistsError
from libcloud.storage.types import ContainerDoesNotExistError
from libcloud.storage.types import ObjectDoesNotExistError
from libcloud.storage.types import Provider
from xtarfile import open as tarfile_open
from xtarfile.xtarfile import SUPPORTED_FORMATS

from opwen_email_server.utils.log import LogMixin
from opwen_email_server.utils.serialization import from_msgpack_bytes
from opwen_email_server.utils.serialization import gunzip_bytes
from opwen_email_server.utils.serialization import gzip_bytes
from opwen_email_server.utils.serialization import to_msgpack_bytes
from opwen_email_server.utils.temporary import create_tempfilename
from opwen_email_server.utils.temporary import removing

AccessInfo = namedtuple('AccessInfo', ['account', 'key', 'container'])

Upload = Tuple[str, Iterable[dict], Callable[[dict], bytes]]
Download = Tuple[str, Callable[[bytes], dict]]


class _Container:
    def __init__(self, wrapped: Container):
        self._wrapped = wrapped

    def get_object(self, object_name: str) -> Object:
        return self._wrapped.get_object(object_name)

    def iterate_objects(self, prefix: Optional[str] = None) -> Iterable[Object]:
        return self._wrapped.iterate_objects(prefix)

    def upload_object(self, file_path: str, object_name: str) -> Object:
        return self._wrapped.upload_object(file_path, object_name)

    def upload_object_via_stream(self, iterator: Iterator[bytes], object_name: str) -> Object:
        return self._wrapped.upload_object_via_stream(iterator, object_name)


class _CaseInsensitiveContainer(_Container):
    def get_object(self, object_name: str) -> Object:
        object_name = object_name.lower()
        return super().get_object(object_name)

    def iterate_objects(self, prefix: Optional[str] = None) -> Iterable[Object]:
        prefix = prefix.lower() if prefix is not None else None
        return super().iterate_objects(prefix)

    def upload_object(self, file_path: str, object_name: str) -> Object:
        object_name = object_name.lower()
        return super().upload_object(file_path, object_name)

    def upload_object_via_stream(self, iterator: Iterator[bytes], object_name: str) -> Object:
        object_name = object_name.lower()
        return super().upload_object_via_stream(iterator, object_name)


class _BaseAzureStorage(LogMixin):
    def __init__(self,
                 account: str,
                 key: str,
                 container: str,
                 provider: str,
                 host: Optional[str] = None,
                 secure: bool = True,
                 case_sensitive: bool = True) -> None:
        self._account = account
        self._key = key
        self._container = container
        self._provider = getattr(Provider, provider)
        self._host = host or None
        self._secure = secure
        self._case_sensitive = case_sensitive

    @cached_property
    def _driver(self) -> StorageDriver:
        driver = get_driver(self._provider)
        return driver(self._account, self._key, host=self._host, secure=self._secure)

    @cached_property
    def _client(self) -> _Container:
        try:
            container = self._driver.get_container(self._container)
        except ContainerDoesNotExistError:
            try:
                container = self._driver.create_container(self._container)
            except ContainerAlreadyExistsError:
                container = self._driver.get_container(self._container)
        return _Container(container) if self._case_sensitive else _CaseInsensitiveContainer(container)

    @property
    def _generated_suffix(self) -> str:
        return ''

    def access_info(self) -> AccessInfo:
        return AccessInfo(
            account=self._account,
            key=self._key,
            container=self._container,
        )

    def ensure_exists(self):
        # noinspection PyStatementEffect
        self._client

    def delete(self, resource_id: str):
        try:
            resource = self._client.get_object(resource_id)
        except ObjectDoesNotExistError:
            self.log_warning('deleted missing %s', resource_id)
        else:
            resource.delete()
            self.log_debug('deleted %s', resource_id)

    def iter(self, prefix: Optional[str] = None) -> Iterator[str]:
        resources = self._client.iterate_objects(prefix=prefix)

        for resource in resources:
            resource_id = resource.name

            if prefix is not None:
                resource_id = resource_id[len(prefix):]

            if resource_id.endswith(self._generated_suffix):
                resource_id = resource_id[:-len(self._generated_suffix)]

            yield resource_id
            self.log_debug('listed %s', resource_id)


class AzureFileStorage(_BaseAzureStorage):
    def store_file(self, resource_id: str, path: str):
        self.log_debug('storing file %s at %s', path, resource_id)
        self._client.upload_object(path, resource_id)

    def fetch_file(self, resource_id: str) -> str:
        resource = self._client.get_object(resource_id)
        path = create_tempfilename(resource_id)
        resource.download(path)
        self.log_debug('fetched file %s from %s', path, resource_id)
        return path


class _AzureBytesStorage(_BaseAzureStorage):
    _compression = 'gz'

    def store_bytes(self, resource_id: str, content: bytes):
        filename = self._to_filename(resource_id)
        self.log_debug('storing %d bytes at %s', len(content), filename)
        upload = BytesIO()
        upload.write(gzip_bytes(content))
        upload.seek(0)
        self._client.upload_object_via_stream(upload, filename)

    def fetch_bytes(self, resource_id: str) -> bytes:
        filename = self._to_filename(resource_id)
        download = BytesIO()
        resource = self._client.get_object(filename)
        for chunk in resource.as_stream():
            download.write(chunk)
        download.seek(0)
        content = gunzip_bytes(download.read())
        self.log_debug('fetched %d bytes from %s', len(content), filename)
        return content

    def delete(self, resource_id: str):
        filename = self._to_filename(resource_id)
        super().delete(filename)

    def _to_filename(self, resource_id: str) -> str:
        if resource_id.endswith(self._generated_suffix):
            return resource_id
        return f'{resource_id}{self._generated_suffix}'

    @property
    def _generated_suffix(self) -> str:
        return f'.{self._extension}.{self._compression}'

    @property
    def _extension(self) -> str:
        raise NotImplementedError  # pragma: no cover


class AzureTextStorage(_AzureBytesStorage):
    _encoding = 'utf-8'
    _extension = 'txt'

    def store_text(self, resource_id: str, text: str):
        content = text.encode(self._encoding)
        self.store_bytes(resource_id, content)

    def fetch_text(self, resource_id: str) -> str:
        content = self.fetch_bytes(resource_id)
        return content.decode(self._encoding)


class AzureObjectsStorage(LogMixin):
    _compression = 'zstd'
    _compression_level = 20

    def __init__(self, file_storage: AzureFileStorage, resource_id_source: Callable[[], str]):
        self._file_storage = file_storage
        self._resource_id_source = resource_id_source

    def _open_archive_file(self, archive: TarFile, name: str) -> IO[bytes]:
        while True:
            member = archive.next()
            if member is None:
                break
            if member.name == name:
                fobj = archive.extractfile(member)
                if fobj is None:
                    break
                return fobj

        # noinspection PyProtectedMember
        raise ObjectDoesNotExistError(f'File {name} is missing in archive', self._file_storage._driver, archive.name)

    @classmethod
    def _open_archive(cls, path: str, mode: str) -> TarFile:
        extension_index = path.rfind('.')
        if extension_index > -1:
            compression = path[extension_index + 1:]
        else:
            compression = cls._compression

        kwargs = {}
        if compression == 'zstd' and mode == 'w':
            kwargs['level'] = cls._compression_level

        mode = f'{mode}|{compression}'
        return tarfile_open(path, mode, **kwargs)

    def access_info(self) -> AccessInfo:
        return self._file_storage.access_info()

    def ensure_exists(self):
        return self._file_storage.ensure_exists()

    @classmethod
    def compression_formats(cls) -> Iterable[str]:
        return SUPPORTED_FORMATS

    def store_objects(self, upload: Upload, compression: Optional[str] = None) -> Optional[str]:

        compression = compression or self._compression

        resource_id = f'{self._resource_id_source()}.tar.{compression}'

        name, objs, encoder = upload

        num_stored = 0
        with removing(create_tempfilename(resource_id)) as path:
            with self._open_archive(path, 'w') as archive:
                with NamedTemporaryFile() as fobj:
                    num_bytes = 0
                    for obj in objs:
                        encoded = encoder(obj)
                        fobj.write(encoded)
                        num_bytes += len(encoded)
                        num_stored += 1

                    if num_bytes > 0:
                        fobj.seek(0)
                        archive.add(fobj.name, name)

            if num_stored > 0:
                self._file_storage.store_file(resource_id, path)

        self.log_debug('stored %d objects at %s', num_stored, resource_id)
        return resource_id if num_stored > 0 else None

    def fetch_objects(self, resource_id: str, download: Download) -> Iterable[dict]:

        name, decoder = download

        num_fetched = 0
        with removing(self._file_storage.fetch_file(resource_id)) as path:
            with self._open_archive(path, 'r') as archive:
                fobj = self._open_archive_file(archive, name)
                for encoded in fobj:
                    obj = decoder(encoded)
                    if obj is None:
                        continue
                    num_fetched += 1
                    yield obj
        self.log_debug('fetched %d objects from %s', num_fetched, resource_id)

    def delete(self, resource_id: str):
        self._file_storage.delete(resource_id)


class AzureObjectStorage(_AzureBytesStorage):
    _extension = 'msgpack'

    def fetch_object(self, resource_id: str) -> dict:
        serialized = self.fetch_bytes(resource_id)
        return from_msgpack_bytes(serialized)

    def store_object(self, resource_id: str, obj: dict) -> None:
        serialized = to_msgpack_bytes(obj)
        self.store_bytes(resource_id, serialized)
