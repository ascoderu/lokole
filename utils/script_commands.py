from argparse import FileType
import random
import re
import sys

from babel.messages.frontend import CommandLineInterface
from flask_script import Command
from flask_script import Option

from ascoderu_webapp import db
from ascoderu_webapp.models import Email
from ascoderu_webapp.models import User


class BabelCommand(Command):
    capture_all_args = True

    def run(self, args):
        args.insert(0, sys.argv[0])
        cli = CommandLineInterface()
        cli.run(args)


class GenerateEmailsCommand(Command):
    option_list = (
        Option('--path-to-source-text', '-p',
               dest='text_file', type=FileType('rb')),
        Option('--number-of-emails-to-generate', '-n',
               dest='num_emails', type=int),
    )

    @classmethod
    def _read_text(cls, text_file, encoding='utf8'):
        text = text_file.read()
        text_file.close()

        text = text.decode(encoding)
        text = ' '.join(text.splitlines())
        text = re.sub('\s+', ' ', text)
        return text

    @classmethod
    def _split_sentences(cls, text):
        return re.split('(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)

    @classmethod
    def _random_local_sender(cls):
        user = random.choice(User.query.all())
        return user.email or user.name

    @classmethod
    def _random_email_addresses(cls):
        addresses = (
            'random@randomtestemail.net',
            'foo@randomtestemail.net',
            'bar@randomtestemail.net',
            'baz@randomtestemail.net',
        )
        num_addressees = random.randint(1, len(addresses))
        return random.sample(addresses, num_addressees)

    @classmethod
    def _create_random_email(cls, sentences, min_sents=3, max_sents=20):
        num_sentences = random.randint(min_sents, max_sents)
        email_sentences = iter(random.sample(sentences, num_sentences))
        return Email(
            date=None,
            sender=cls._random_local_sender(),
            to=cls._random_email_addresses(),
            subject=next(email_sentences),
            body='\n'.join(email_sentences)
        )

    def run(self, text_file, num_emails):
        text = self._read_text(text_file)
        sentences = self._split_sentences(text)
        for _ in range(num_emails):
            email = self._create_random_email(sentences)
            db.session.add(email)
        db.session.commit()
