from typing import Callable
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional

from libcloud.storage.types import ObjectDoesNotExistError
from requests import RequestException
from requests import post as http_post

from opwen_email_server.constants import events
from opwen_email_server.constants import github
from opwen_email_server.services.storage import AzureObjectStorage
from opwen_email_server.utils.log import LogMixin


class AnyOfBasicAuth(LogMixin):
    def __init__(self, auths: Iterable[Callable[[str, str, Optional[List[str]]], Optional[Dict[str, str]]]]):
        self._auths = list(auths)

    def __call__(self, username, password, required_scopes=None):
        for auth in self._auths:
            user = auth(username, password, required_scopes)
            if user is not None:
                return user

        return None


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

        if not self._has_scopes(user, required_scopes):
            self.log_event(events.MISSING_SCOPES, {'username': username})  # noqa: E501  # yapf: disable
            return None

        return {'sub': username}

    @classmethod
    def _has_scopes(cls, user, required_scopes) -> bool:
        if not required_scopes:
            return True

        return set(required_scopes).issubset(user.get('scopes', []))


class GithubBasicAuth(LogMixin):
    def __init__(self, organization: str, team: str, page_size: int = 50):
        self._organization = organization
        self._team = team
        self._page_size = page_size

    def __call__(self, username, password, required_scopes=None):
        if not username or not password or not self._organization or not self._team:
            return None

        try:
            team_members = self._fetch_team_members(access_token=password)
            user_exists = any(username == team_member for team_member in team_members)
        except RequestException:
            self.log_event(events.BAD_PASSWORD, {'username': username})  # noqa: E501  # yapf: disable
            return None

        if not user_exists:
            self.log_event(events.UNKNOWN_USER, {'username': username})  # noqa: E501  # yapf: disable
            return None

        return {'sub': username}

    def _fetch_team_members(self, access_token: str) -> Iterable[str]:
        cursor = None

        while True:
            response = http_post(
                url=github.GRAPHQL_URL,
                json={
                    'query': '''
                        query($organization:String!, $team:String!, $cursor:String, $first:Int!) {
                            organization(login:$organization) {
                                team(slug:$team) {
                                    members(after:$cursor, first:$first, orderBy:{ field:LOGIN, direction:DESC }) {
                                        edges {
                                            cursor
                                        }
                                        nodes {
                                            login
                                        }
                                    }
                                }
                            }
                        }
                    ''',
                    'variables': {
                        'organization': self._organization,
                        'team': self._team,
                        'cursor': cursor,
                        'first': self._page_size,
                    },
                },
                headers={
                    'Authorization': f'Bearer {access_token}',
                },
            )
            response.raise_for_status()

            members = response.json()['data']['organization']['team']['members']
            nodes = members['nodes']
            edges = members['edges']

            for member in nodes:
                yield member['login']

            if len(nodes) < self._page_size:
                break

            cursor = edges[-1]['cursor']


class AzureAuth(LogMixin):
    def __init__(self, storage: AzureObjectStorage) -> None:
        self._storage = storage

    def insert(self, client_id: str, domain: str, owner: str):
        auth = {'client_id': client_id, 'owner': owner, 'domain': domain}
        self._storage.store_object(self._client_id_file(client_id), auth)
        self._storage.store_object(self._domain_file(domain), auth)
        self.log_info('Registered client %s at domain %s', client_id, domain)

    def is_owner(self, domain: str, username: str) -> bool:
        try:
            auth = self._storage.fetch_object(self._domain_file(domain))
        except ObjectDoesNotExistError:
            self.log_warning('Unrecognized domain %s', domain)
            return False

        return auth.get('owner') == username

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


class NoAuth(LogMixin):
    def is_owner(self, domain: str, username: str) -> bool:
        return True

    def domain_for(self, client_id: str) -> str:
        return 'service'
