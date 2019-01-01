from abc import ABCMeta
from abc import abstractmethod
from os import getenv
from os import path
from urllib.parse import urlencode

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
    def __init__(self, compression: str, hostname: str, client_id: str):
        self._compression = compression
        self._hostname = hostname
        self._client_id = client_id

    @property
    def _base_url(self) -> str:
        return 'http://{hostname}/api/email'.format(
            hostname=self._hostname)

    @property
    def _upload_url(self) -> str:
        return '{base_url}/upload/{client_id}'.format(
            base_url=self._base_url,
            client_id=self._client_id)

    @property
    def _download_url(self) -> str:
        return '{base_url}/download/{client_id}?{query}'.format(
            base_url=self._base_url,
            client_id=self._client_id,
            query=urlencode({
                'compression': self._compression,
            }))

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
