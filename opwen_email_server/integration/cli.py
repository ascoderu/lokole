import click

from opwen_email_server import config


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


if __name__ == '__main__':
    cli()
