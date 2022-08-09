from importlib import import_module

from cached_property import cached_property

from opwen_email_client.domain.email.client import HttpEmailServerClient
from opwen_email_client.domain.email.client import LocalEmailServerClient
from opwen_email_client.domain.email.sql_store import SqliteEmailStore
from opwen_email_client.domain.email.sync import AzureSync
from opwen_email_client.util.serialization import JsonSerializer
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.forms.login import LoginForm
from opwen_email_client.webapp.login import FlaskLoginUserStore


class Ioc:

    @cached_property
    def email_store(self):
        return SqliteEmailStore(
            page_size=AppConfig.EMAILS_PER_PAGE,
            restricted={AppConfig.NEWS_INBOX: AppConfig.NEWS_SENDERS},
            database_path=AppConfig.LOCAL_EMAIL_STORE,
        )

    @cached_property
    def email_sync(self):
        if AppConfig.TESTING:
            email_server_client = LocalEmailServerClient()
        else:
            if AppConfig.EMAIL_SERVER_ENDPOINT:
                endpoint = AppConfig.EMAIL_SERVER_ENDPOINT
            elif AppConfig.EMAIL_SERVER_HOSTNAME:
                endpoint = 'https://{}'.format(AppConfig.EMAIL_SERVER_HOSTNAME)
            else:
                endpoint = None

            email_server_client = HttpEmailServerClient(
                compression=AppConfig.COMPRESSION,
                endpoint=endpoint,
                client_id=AppConfig.CLIENT_ID,
            )

        serializer = JsonSerializer()

        return AzureSync(
            compression=AppConfig.COMPRESSION,
            account_name=AppConfig.STORAGE_ACCOUNT_NAME,
            account_key=AppConfig.STORAGE_ACCOUNT_KEY,
            account_host=AppConfig.STORAGE_ACCOUNT_HOST,
            account_secure=AppConfig.STORAGE_ACCOUNT_SECURE,
            email_server_client=email_server_client,
            container=AppConfig.STORAGE_CONTAINER,
            provider=AppConfig.STORAGE_PROVIDER,
            serializer=serializer,
        )

    @cached_property
    def user_store(self):
        return FlaskLoginUserStore()

    @cached_property
    def login_form(self):
        return LoginForm


def _new_ioc(fqn: str) -> Ioc:
    fqn_parts = fqn.split('.')
    class_name = fqn_parts.pop()
    module_name = '.'.join(fqn_parts)

    module = import_module(module_name)
    cls = getattr(module, class_name)

    return cls()
