import sys

from babel.messages.frontend import CommandLineInterface
from flask_script import Command


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
