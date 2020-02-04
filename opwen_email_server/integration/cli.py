from urllib.parse import unquote
from urllib.parse import urlparse

import click
from azure.servicebus import ServiceBusClient

from opwen_email_server import config

_QUEUES = (
    config.REGISTER_CLIENT_QUEUE,
    config.INBOUND_STORE_QUEUE,
    config.WRITTEN_STORE_QUEUE,
    config.SEND_QUEUE,
    config.MAILBOX_RECEIVED_QUEUE,
    config.MAILBOX_SENT_QUEUE,
)


@click.group()
def cli():
    pass


@cli.command()
@click.option('--separator', '-s', default='\n')
def print_queues(separator):
    click.echo(separator.join(_QUEUES))


@cli.command()
@click.option('--queues', '-q', default=_QUEUES, multiple=True)
def delete_queues(queues):
    queue_broker = urlparse(config.QUEUE_BROKER)
    if queue_broker.scheme != 'azureservicebus':
        click.echo(f'Skipping queue cleanup for {queue_broker.scheme}')
        return

    client = ServiceBusClient(
        service_namespace=queue_broker.hostname,
        shared_access_key_name=unquote(queue_broker.username),
        shared_access_key_value=unquote(queue_broker.password),
    )

    for queue in queues:
        click.echo(f'Deleting queue {queue}')
        client.delete_queue(queue)


if __name__ == '__main__':
    cli()
