#!/usr/bin/env python3

from argparse import ArgumentParser

from opwen_email_server import azure_constants as constants
from opwen_email_server import config
from opwen_email_server.services.auth import AzureAuth
from opwen_email_server.services.storage import AzureFileStorage
from opwen_email_server.services.storage import AzureObjectStorage
from opwen_email_server.services.storage import AzureTextStorage

parser = ArgumentParser()
parser.add_argument('--tables_account', default=config.TABLES_ACCOUNT)
parser.add_argument('--tables_key', default=config.TABLES_KEY)
parser.add_argument('--client_account', default=config.CLIENT_STORAGE_ACCOUNT)
parser.add_argument('--client_key', default=config.CLIENT_STORAGE_KEY)
parser.add_argument('--table', default=constants.TABLE_AUTH)
parser.add_argument('--container', default=constants.CONTAINER_CLIENT_PACKAGES)
parser.add_argument('--provider', default=config.STORAGE_PROVIDER)
parser.add_argument('--client', required=True)
parser.add_argument('--domain', required=True)
args = parser.parse_args()

auth = AzureAuth(
    storage=AzureTextStorage(
        account=args.tables_account,
        key=args.tables_key,
        container=args.table,
        provider=args.provider))

auth.insert(client_id=args.client, domain=args.domain)

# noinspection PyStatementEffect,PyProtectedMember
# hack to ensure that the container gets created before the client accesses it
storage = AzureObjectStorage(
    file_storage=AzureFileStorage(
        account=args.client_account,
        key=args.client_key,
        container=args.container,
        provider=args.provider))._file_storage._client
