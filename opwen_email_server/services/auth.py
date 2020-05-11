from typing import Iterable
from typing import Iterator
from typing import Optional

from libcloud.storage.types import ObjectDoesNotExistError
from requests import RequestException
from requests import post as http_post

from opwen_email_server.constants import events
from opwen_email_server.constants import github
from opwen_email_server.services.storage import AzureObjectStorage
from opwen_email_server.utils.log import LogMixin


class BasicAuth(LogMixin):
    def __init__(self, users: dict):
        self._users = dict(users)

    def __call__(self, username, password, required_scopes=None):
        if not username or not password:
            return None

        try:
            user = self._users[username]
        except KeyError:
            self.log_event(events.UNKNOWN_USER, {'username': username})  # noqa: E501  # yapf: disable
            return None

        if user['password'] != password:
            self.log_event(events.BAD_PASSWORD, {'username': username})  # noqa: E501  # yapf: disable
            return None

        scopes = user.get('scopes', [])

        return {'sub': {'name': username, 'scopes': scopes}, 'scope': scopes}


class GithubAuth(LogMixin):
    def __init__(self, organization: str, page_size: int = 50):
        self._organization = organization
        self._page_size = page_size

    def __call__(self, access_token, required_scopes=None):
        if not access_token or not self._organization:
            return None

        try:
            query = self._query_github(access_token)
            login = next(query)
            scopes = list(query)
        except RequestException:
            self.log_event(events.BAD_PASSWORD, {'username': 'access_token'})  # noqa: E501  # yapf: disable
            return None

        return {'sub': {'name': login, 'scopes': scopes}, 'scope': scopes}

    def _query_github(self, access_token: str) -> Iterator[str]:
        cursor = None

        while True:
            response = http_post(
                url=github.GRAPHQL_URL,
                json={
                    'query': '''
                        query($organization:String!, $cursor:String, $first:Int!) {
                            viewer {
                                login
                                organization(login:$organization) {
                                    teams(after:$cursor, first:$first, orderBy:{ field:NAME, direction:DESC }) {
                                        edges {
                                            cursor
                                        }
                                        nodes {
                                            slug
                                        }
                                    }
                                }
                            }
                        }
                    ''',
                    'variables': {
                        'organization': self._organization,
                        'cursor': cursor,
                        'first': self._page_size,
                    },
                },
                headers={
                    'Authorization': f'Bearer {access_token}',
                },
            )
            response.raise_for_status()

            viewer = response.json()['data']['viewer']
            teams = viewer['organization']['teams']
            nodes = teams['nodes']
            edges = teams['edges']

            yield viewer['login']

            for team in nodes:
                yield team['slug']

            if len(nodes) < self._page_size:
                break

            cursor = edges[-1]['cursor']


class Auth:
    def insert(self, client_id: str, domain: str, owner: dict) -> None:
        raise NotImplementedError  # pragma: no cover

    def delete(self, client_id: str, domain: str) -> bool:
        raise NotImplementedError  # pragma: no cover

    def is_owner(self, domain: str, user: dict) -> bool:
        raise NotImplementedError  # pragma: no cover

    def client_id_for(self, domain: str) -> Optional[str]:
        raise NotImplementedError  # pragma: no cover

    def domain_for(self, client_id: str) -> Optional[str]:
        raise NotImplementedError  # pragma: no cover

    def domains(self) -> Iterable[str]:
        raise NotImplementedError  # pragma: no cover


class AzureAuth(Auth, LogMixin):
    def __init__(self, storage: AzureObjectStorage, sudo_scope: str) -> None:
        self._storage = storage
        self._sudo_scope = sudo_scope

    def insert(self, client_id: str, domain: str, owner: dict) -> None:
        auth = {'client_id': client_id, 'owner': owner['name'], 'domain': domain}
        self._storage.store_object(self._client_id_file(client_id), auth)
        self._storage.store_object(self._domain_file(domain), auth)
        self.log_info('Registered client %s at domain %s', client_id, domain)

    def is_owner(self, domain: str, user: dict) -> bool:
        if self._sudo_scope in user.get('scopes', []):
            return True

        try:
            auth = self._storage.fetch_object(self._domain_file(domain))
        except ObjectDoesNotExistError:
            self.log_warning('Unrecognized domain %s', domain)
            return False

        return auth.get('owner') == user['name']

    def delete(self, client_id: str, domain: str) -> bool:
        self._storage.delete(self._domain_file(domain))
        self._storage.delete(self._client_id_file(client_id))
        return True

    def client_id_for(self, domain: str) -> Optional[str]:
        try:
            auth = self._storage.fetch_object(self._domain_file(domain))
        except ObjectDoesNotExistError:
            self.log_warning('Unrecognized domain %s', domain)
            return None

        client_id = auth['client_id']

        self.log_debug('Domain %s has client %s', domain, client_id)
        return client_id

    def domain_for(self, client_id: str) -> Optional[str]:
        try:
            auth = self._storage.fetch_object(self._client_id_file(client_id))
        except ObjectDoesNotExistError:
            self.log_warning('Unrecognized client %s', client_id)
            return None
        else:
            domain = auth['domain']
            self.log_debug('Client %s has domain %s', client_id, domain)
            return domain

    def domains(self) -> Iterable[str]:
        return self._storage.iter(self._domain_file(''))

    @classmethod
    def _domain_file(cls, domain: str) -> str:
        return f'domain/{domain}'

    @classmethod
    def _client_id_file(cls, client_id: str) -> str:
        return f'client_id/{client_id}'


class NoAuth(Auth):
    def __init__(self, client_id: str = 'service', domain: str = 'service'):
        self._client_id = client_id
        self._domain = domain

    def insert(self, client_id: str, domain: str, owner: dict) -> None:
        pass

    def delete(self, client_id: str, domain: str) -> bool:
        return False

    def client_id_for(self, domain: str) -> Optional[str]:
        return self._client_id

    def domains(self) -> Iterable[str]:
        return []

    def is_owner(self, domain: str, user: dict) -> bool:
        return True

    def domain_for(self, client_id: str) -> str:
        return self._domain
