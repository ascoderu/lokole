from setuptools import find_packages
from setuptools import setup


with open('requirements.txt') as fobj:
    install_requires = [line.strip() for line in fobj]


with open('README.rst') as fobj:
    long_description = fobj.read()


with open('version.txt') as fobj:
    version = fobj.read().strip()


packages = find_packages(exclude=['tests*'])
scripts = [
    'registerclient.py',
]


setup(
    name='opwen_email_server',
    version=version,
    author='Clemens Wolff',
    author_email='clemens.wolff+pypi@gmail.com',
    packages=packages,
    url='https://github.com/ascoderu/opwen-cloudserver',
    license='Apache Software License',
    description='Email server for the Lokole project: https://ascoderu.ca',
    long_description=long_description,
    scripts=scripts,
    include_package_data=True,
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Topic :: Communications :: Email',
    ])
