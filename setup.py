from setuptools import find_packages
from setuptools import setup


with open('requirements.txt') as fobj:
    install_requires = [line.strip() for line in fobj]


with open('README.rst') as fobj:
    long_description = fobj.read()


with open('version.txt') as fobj:
    version = fobj.read().strip()


packages = find_packages(exclude=['tests*'])
scripts = ['manage.py']


setup(
    name='opwen_email_client',
    version=version,
    author='Clemens Wolff',
    author_email='clemens.wolff+pypi@gmail.com',
    packages=packages,
    url='https://github.com/ascoderu/opwen-webapp',
    license='License :: OSI Approved :: Apache Software License',
    description='Email client for the Opwen project',
    long_description=long_description,
    include_package_data=True,
    scripts=scripts,
    install_requires=install_requires)
