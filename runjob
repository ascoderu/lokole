#!/usr/bin/env python3
from importlib import import_module
from os.path import dirname
from os.path import join


def _load_environment():
    try:
        # noinspection PyUnresolvedReferences
        from dotenv import load_dotenv
        load_dotenv(join(dirname(__file__), '.env'))
    except ImportError:
        pass


def _module_for(job_name: str) -> str:
    return 'opwen_email_server.jobs.{}'.format(job_name)


def _main(job_name: str):
    _load_environment()

    try:
        job_module = import_module(_module_for(job_name))
        job_factory = getattr(job_module, 'Job')
    except AttributeError:
        raise ValueError('The job {} does not exist'.format(job_name))

    job = job_factory()
    job.run_forever()


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('job_name')
    args = parser.parse_args()

    _main(args.job_name)
