from argparse import FileType
from datetime import datetime
from functools import lru_cache
import random
import re
import sys

from babel.messages.frontend import CommandLineInterface
from flask_script import Command
from flask_script import Option

from ascoderu_webapp import db
from ascoderu_webapp import user_datastore
from ascoderu_webapp.models import Email
from ascoderu_webapp.models import User


class BabelCommand(Command):
    capture_all_args = True

    def run(self, args):
        args.insert(0, sys.argv[0])
        cli = CommandLineInterface()
        cli.run(args)


class PopulateDatabaseWithTestEntriesCommand(Command):
    option_list = (
        Option('--path-to-source-text', '-p', default=None,
               dest='text_file', type=FileType('rb')),
        Option('--number-of-emails-to-generate', '-n', default=25,
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
    @lru_cache(maxsize=None)
    def _all_local_senders(cls):
        users = User.query.all()
        return [user.email or user.name for user in users]

    @classmethod
    def _random_local_sender(cls):
        return random.choice(cls._all_local_senders())

    @classmethod
    def _random_email_addresses(cls):
        addresses = [
            'random@randomtestemail.net',
            'foo@randomtestemail.net',
            'bar@randomtestemail.net',
            'baz@randomtestemail.net',
        ] + cls._all_local_senders()

        num_addressees = random.randint(1, len(addresses))
        return random.sample(addresses, num_addressees)

    @classmethod
    def _create_random_email(cls, sentences, min_sents=3, max_sents=20):
        num_sentences = random.randint(min_sents, max_sents)
        email_sentences = iter(random.sample(sentences, num_sentences))
        subj = next(email_sentences)
        body = '\n'.join(email_sentences)

        sender = cls._random_local_sender()
        to = cls._random_email_addresses()
        if all(addressee in cls._all_local_senders() for addressee in to):
            date = datetime.utcnow()
        else:
            date = None

        return Email(date=date, sender=sender, to=to, subject=subj, body=body)

    @classmethod
    def _populate_emails(cls, text_file, num_emails):
        if not text_file or not num_emails:
            return

        text = cls._read_text(text_file)
        sentences = cls._split_sentences(text)
        for _ in range(num_emails - Email.query.count()):
            email = cls._create_random_email(sentences)
            db.session.add(email)
        db.session.commit()

    @classmethod
    def _populate_users(cls):
        if not User.query.filter_by(name='test').first():
            user_datastore.create_user(name='test', password='test')
            db.session.commit()

        if not User.query.filter_by(email='test@test.net').first():
            user_datastore.create_user(email='test@test.net', password='test')
            db.session.commit()

    def run(self, text_file, num_emails):
        self._populate_users()
        self._populate_emails(text_file, num_emails)
