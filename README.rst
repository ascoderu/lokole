Opwen cloudserver
=================

.. image:: https://travis-ci.org/ascoderu/opwen-cloudserver.svg?branch=master
  :target: https://travis-ci.org/ascoderu/opwen-cloudserver

.. image:: https://img.shields.io/pypi/v/opwen_email_server.svg
  :target: https://pypi.python.org/pypi/opwen_email_server/

What's this?
------------

This repository contains the source code for the Opwen cloud server. Its purpose
is to connect the `application <https://github.com/ascoderu/opwen-webapp>`_
running on the Opwen Lokole devices to the rest of the world.

The server has two main responsibilities:

1. Receive emails from the internet that are addressed to Lokole users and
   forward them to the appropriate Lokole device.
2. Send new emails created by Lokole users to the rest of the internet.

This package is intended to run on an Ubuntu server. There is a `script <https://github.com/ascoderu/opwen-setup/blob/master/setup-cloudserver.sh>`_
to set up a server with all the bits and pieces necessary for deployment.

System overview
---------------

.. image:: docs/system-overview.png
  :width: 800
  :align: center
  :alt: Overview of the Lokole system
  :target: https://raw.githubusercontent.com/ascoderu/opwen-cloudserver/master/docs/system-overview.png

Data exchange format
--------------------

In order to communicate between the Opwen cloud server and the Opwen
web-application (aka Lokole), a protocol based on gzipped jsonl files uploaded
to Azure Blob Storage is used. The files contains a JSON object per line.
Each JSON object describes an email, using the following schema:

.. sourcecode :: json

  {
    "sent_at": "yyyy-mm-dd HH:MM",
    "to": ["email"],
    "cc": ["email"],
    "bcc": ["email"],
    "from": "email",
    "subject": "string",
    "body": "html",
    "attachments": [{"filename": "string", "content": "base64"}]
  }

Development setup
-----------------

First, get the source code.

.. sourcecode :: sh

  git clone git@github.com:ascoderu/opwen-cloudserver.git

Second, install the system-level dependencies using your package manager.

.. sourcecode :: sh

  sudo dnf install python3-devel
  sudo dnf install openssl-devel

Third, use the makefile to verify your installation by running the tests and
starting up the server. The makefile will automatically install all required
dependencies into a virtual environment.

.. sourcecode :: sh

  cd opwen-cloudserver

  make tests
  make server
  make workers

There is an `OpenAPI specification <https://github.com/ascoderu/opwen-cloudserver/blob/master/opwen_email_server/static/email-api-spec.yaml>`_
that documents the functionality of the application and provides pointers to the
entry points into the code.
