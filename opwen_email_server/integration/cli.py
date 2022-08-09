import click
from azure.servicebus.management import ServiceBusAdministrationClient
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
            config.PROCESS_SERVICE_QUEUE,
            config.SEND_QUEUE,
            config.MAILBOX_RECEIVED_QUEUE,
            config.MAILBOX_SENT_QUEUE,
        )))


@cli.command()
@click.option('-s', '--suffix', default='')
def delete_queues(suffix):

    if config.QUEUE_BROKER_SCHEME != 'azureservicebus':
        click.echo(f'Skipping queue cleanup for {config.QUEUE_BROKER_SCHEME}')
        return

    # https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/servicebus/azure-servicebus/migration_guide.md#working-with-administration-client
    connection_string = f"Endpoint=sb://{config.QUEUE_BROKER_HOST}.servicebus.windows.net/;" \
                        f"SharedAccessKeyName={config.QUEUE_BROKER_USERNAME};" \
                        f"SharedAccessKey={config.QUEUE_BROKER_PASSWORD}"

    with ServiceBusAdministrationClient.from_connection_string(connection_string) as servicebus_mgmt_client:
        for queue in servicebus_mgmt_client.list_queues():
            if queue.name.endswith(suffix):
                click.echo(f'Deleting queue {queue.name}')
                servicebus_mgmt_client.delete_queue(queue.name)


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
