from abc import ABCMeta
from abc import abstractmethod
from typing import Tuple

import requests


class EmailServerClient(metaclass=ABCMeta):
    @abstractmethod
    def upload(self, resource_id: str, container: str):
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def download(self) -> Tuple[str, str]:
        raise NotImplementedError  # pragma: no cover


class HttpEmailServerClient(EmailServerClient):
    _supported_resource_type = 'azure-blob'

    def __init__(self, read_api: str, write_api: str, client_id: str):
        self._read_api = read_api
        self._write_api = write_api
        self._client_id = client_id

    @property
    def _upload_url(self) -> str:
        return 'http://{host}/api/email/lokole'.format(
            host=self._write_api)

    @property
    def _download_url(self) -> str:
        return 'http://{host}/api/email/lokole'.format(
            host=self._read_api)

    @property
    def _auth_headers(self) -> dict:
        return {
            'X-LOKOLE-ClientId': self._client_id,
        }

    def upload(self, resource_id, container):
        payload = {
            'resource_id': resource_id,
            'container_name': container,
            'resource_type': self._supported_resource_type,
        }

        response = requests.post(self._upload_url, json=payload,
                                 headers=self._auth_headers)
        response.raise_for_status()

    def download(self):
        response = requests.get(self._download_url, headers=self._auth_headers)
        response.raise_for_status()

        payload = response.json()
        return payload['resource_id'], payload['resource_container']
