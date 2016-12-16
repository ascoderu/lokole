import sys
from logging import getLogger

from babel.messages.frontend import CommandLineInterface
from flask_script import Command

from opwen_email_client.actions import SyncEmails
from opwen_email_client.config import AppConfig
from opwen_email_client.ioc import Ioc
from opwen_infrastructure.cron import CronCommand
from opwen_infrastructure.cron import CronCommandMixin


class BabelCommand(Command):
    capture_all_args = True

    # pylint: disable=arguments-differ,method-hidden
    # noinspection PyMethodOverriding
    def run(self, args):
        """
        :type args: list[str]

        """
        args.insert(0, sys.argv[0])
        cli = CommandLineInterface()
        cli.run(args)


class SyncDaemonCommand(CronCommandMixin, Command):
    def __init__(self):
        logger = getLogger()
        logger.setLevel(AppConfig.LOG_LEVEL)

        CronCommandMixin.__init__(
            self,
            logger,
            CronCommand(
                description='sync emails with server',
                scheduled_hour_utc=str(AppConfig.EMAIL_SYNC_HOUR_UTC),
                command=SyncEmails(
                    email_sync=Ioc.email_sync,
                    email_store=Ioc.email_store,
                    internet_interface=AppConfig.INTERNET_INTERFACE_NAME)))
