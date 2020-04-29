import re
from pathlib import Path

from setuptools import find_packages
from setuptools import setup

client_package = 'opwen_email_client'
server_package = 'opwen_email_server'
here = Path(__file__).parent


def requirements_for(name):
    with (here / name).open(encoding='utf-8') as req:
        return [line.strip() for line in req]


with (here / 'README.rst').open(encoding='utf-8') as fobj:
    long_description = fobj.read()

with (here / client_package / '__init__.py').open(encoding='utf-8') as fobj:
    version = re.search(r"^__version__ = '([^']*)'",
                        fobj.read(), re.MULTILINE).group(1)

scripts = ['manage.py']

setup(
    name=client_package,
    version=version,
    author='Ascoderu',
    author_email='ascoderu.opwen@gmail.com',
    packages=find_packages(exclude=['tests*']),
    url='https://github.com/ascoderu/lokole',
    license='Apache Software License',
    description='Email client for the Lokole project: https://ascoderu.ca',
    long_description=long_description,
    include_package_data=True,
    scripts=scripts,
    install_requires=requirements_for('requirements-webapp.txt'),
    extras_require={
        server_package: requirements_for('requirements.txt'),
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Topic :: Communications :: Email',
    ])
