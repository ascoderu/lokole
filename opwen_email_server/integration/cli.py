from urllib.parse import unquote
from urllib.parse import urlparse

import click
from azure.servicebus import ServiceBusClient
from libcloud.storage.providers import get_driver

from opwen_email_server import config

_STORAGES = (
    (
        config.BLOBS_ACCOUNT,
        config.BLOBS_KEY,
        config.BLOBS_HOST,
        config.BLOBS_SECURE,
    ),
    (
        config.TABLES_ACCOUNT,
        config.TABLES_KEY,
        config.TABLES_HOST,
        config.TABLES_SECURE,
    ),
    (
        config.CLIENT_STORAGE_ACCOUNT,
        config.CLIENT_STORAGE_KEY,
        config.CLIENT_STORAGE_HOST,
        config.CLIENT_STORAGE_SECURE,
    ),
)


@click.group()
def cli():
    pass


@cli.command()
@click.option('--separator', '-s', default='\n')
def print_queues(separator):
    click.echo(
        separator.join((
            config.REGISTER_CLIENT_QUEUE,
            config.INBOUND_STORE_QUEUE,
            config.WRITTEN_STORE_QUEUE,
            config.SEND_QUEUE,
            config.MAILBOX_RECEIVED_QUEUE,
            config.MAILBOX_SENT_QUEUE,
        )))


@cli.command()
@click.option('-s', '--suffix', default='')
def delete_queues(suffix):
    suffix = suffix.replace('-', '_')

    queue_broker = urlparse(config.QUEUE_BROKER)
    if queue_broker.scheme != 'azureservicebus':
        click.echo(f'Skipping queue cleanup for {queue_broker.scheme}')
        return

    client = ServiceBusClient(
        service_namespace=queue_broker.hostname,
        shared_access_key_name=unquote(queue_broker.username),
        shared_access_key_value=unquote(queue_broker.password),
    )

    for queue in client.list_queues():
        if queue.name.endswith(suffix):
            click.echo(f'Deleting queue {queue.name}')
            client.delete_queue(queue.name)


@cli.command()
@click.option('-s', '--suffix')
def delete_containers(suffix):
    for account, key, host, secure in _STORAGES:
        client = get_driver(config.STORAGE_PROVIDER)(account, key, host=host, secure=secure)

        for container in client.iterate_containers():
            if container.name.endswith(suffix):
                click.echo(f'Deleting container {container.name}')

                response = client.connection.request(
                    f'/{container.name}',
                    params={'restype': 'container'},
                    method='DELETE',
                )

                if response.status != 202:
                    raise ValueError(f'Unable to delete container {container.name}')


if __name__ == '__main__':
    cli()
