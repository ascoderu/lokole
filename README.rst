Opwen cloudserver
=================

.. image:: https://travis-ci.org/ascoderu/opwen-cloudserver.svg?branch=master
  :target: https://travis-ci.org/ascoderu/opwen-cloudserver

.. image:: https://img.shields.io/pypi/v/opwen_email_server.svg
  :target: https://pypi.python.org/pypi/opwen_email_server/

What's this?
------------

This repository contains the source code for the Opwen cloud server. Its purpose
is to connect the `application <https://github.com/ascoderu/opwen-webapp>`_ running
on the Opwen Lokole devices to the rest of the world.

The server has two main responsibilities:

1. Receive emails from the internet that are addressed to Lokole users and
   forward them to the appropriate Lokole device.
2. Send new emails created by Lokole users to the rest of the internet.

This package is intended to run on an Ubuntu server. There is a `script <https://github.com/ascoderu/opwen-setup>`_
to set up a server with all the bits and pieces necessary for deployment.

Technical overview
------------------

Can be found in the `opwen-shared readme <https://github.com/ascoderu/opwen-shared/blob/master/README.rst>`_.

Development setup
-----------------

First, get the source code.

.. sourcecode :: sh

  git clone git@github.com:ascoderu/opwen-cloudserver.git

Second, install the dependencies for the package and verify your checkout by
running the tests.

.. sourcecode :: sh

  cd opwen-cloudserver

  virtualenv -p "$(which python3)" --no-site-packages virtualenv
  . virtualenv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt

  pip install nose
  nosetests

The routes of the app are defined in ``opwen_email_server/views.py`` so take
a look there for an overview of the entrypoints into the code.
