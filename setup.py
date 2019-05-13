import re
from pathlib import Path

from setuptools import find_packages
from setuptools import setup

package = 'opwen_email_client'
here = Path(__file__).parent

with (here / 'requirements.txt').open(encoding='utf-8') as fobj:
    install_requires = [line.strip() for line in fobj]

with (here / 'README.rst').open(encoding='utf-8') as fobj:
    long_description = fobj.read()

with (here / package / '__init__.py').open(encoding='utf-8') as fobj:
    version = re.search(r"^__version__ = '([^']*)'",
                        fobj.read(), re.MULTILINE).group(1)

scripts = ['manage.py']

setup(
    name=package,
    version=version,
    author='Clemens Wolff',
    author_email='clemens.wolff+pypi@gmail.com',
    packages=find_packages(exclude=['tests*']),
    url='https://github.com/ascoderu/opwen-webapp',
    license='Apache Software License',
    description='Email client for the Lokole project: https://ascoderu.ca',
    long_description=long_description,
    include_package_data=True,
    scripts=scripts,
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Topic :: Communications :: Email',
    ])
