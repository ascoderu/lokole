from abc import ABCMeta
from abc import abstractmethod
from os import getenv
from os import path

from requests import get as http_get
from requests import post as http_post


class EmailServerClient(metaclass=ABCMeta):
    @abstractmethod
    def upload(self, resource_id: str, container: str):
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def download(self) -> str:
        raise NotImplementedError  # pragma: no cover


class HttpEmailServerClient(EmailServerClient):
    def __init__(self, read_api: str, write_api: str, client_id: str):
        self._read_api = read_api
        self._write_api = write_api
        self._client_id = client_id

    @property
    def _upload_url(self) -> str:
        return 'http://{host}/api/email/upload/{client_id}'.format(
            client_id=self._client_id,
            host=self._write_api)

    @property
    def _download_url(self) -> str:
        return 'http://{host}/api/email/download/{client_id}'.format(
            client_id=self._client_id,
            host=self._read_api)

    def upload(self, resource_id, container):
        payload = {
            'resource_id': resource_id,
        }

        response = http_post(self._upload_url, json=payload)
        response.raise_for_status()

    def download(self):
        response = http_get(self._download_url)
        response.raise_for_status()
        resource_id = response.json()['resource_id']

        return resource_id


class LocalEmailServerClient(EmailServerClient):
    def __init__(self, *args, **kwargs):
        pass

    def download(self) -> str:
        root = getenv('OPWEN_REMOTE_ACCOUNT_NAME')
        container = getenv('OPWEN_REMOTE_RESOURCE_CONTAINER')
        resource_id = 'sync.tar.gz'
        local_file = path.join(root, container, resource_id)
        if not path.isfile(local_file):
            return ''
        return resource_id

    def upload(self, resource_id: str, container: str):
        print('Uploaded {}/{}'.format(container, resource_id))
