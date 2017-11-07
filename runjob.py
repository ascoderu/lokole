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


def _main(job_name: str, run_once: bool):
    _load_environment()

    try:
        job_module = import_module(_module_for(job_name))
        job_factory = getattr(job_module, 'Job')
    except AttributeError:
        raise ValueError('The job {} does not exist'.format(job_name))

    job = job_factory()
    if run_once:
        job.run_once()
    else:
        job.run_forever()


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('job_name')
    parser.add_argument('--once', action='store_true', default=False)
    args = parser.parse_args()

    _main(args.job_name, args.once)
