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
  cd opwen-cloudserver

Second, install the system-level dependencies using your package manager.

.. sourcecode :: sh

  sudo apt-get install -y python3-dev python3-venv python3-pip openssl-dev jq
  curl -L https://aka.ms/InstallAzureCli | bash

Next, set up the required Azure resources and environment variables:

.. sourcecode :: sh

  # connect to Azure account
  az login
  az account set --subscription "YOUR_SUBSCRIPTION_ID_HERE"

  # define client properties
  client_name="$(whoami | tr -dC 'a-zA-Z0-9')"
  client_id="123456789"

  # create development Azure resources
  location="westus"
  resource_group="opwentest${client_name}"
  storage_name="opwenteststorage${client_name}"
  az group create -n ${resource_group} -l ${location} > /dev/null
  az storage account create -n ${storage_name} -g ${resource_group} -l ${location} --sku Standard_RAGRS > /dev/null

  # setup environment variables
  storage_key="$(az storage account keys list -n ${storage_name} -g ${resource_group} | jq -r '.[0].value')"
  cat > secrets.env << EOF
  LOKOLE_EMAIL_SERVER_AZURE_BLOBS_NAME='${storage_name}'
  LOKOLE_EMAIL_SERVER_AZURE_QUEUES_NAME='${storage_name}'
  LOKOLE_EMAIL_SERVER_AZURE_TABLES_NAME='${storage_name}'
  LOKOLE_CLIENT_AZURE_STORAGE_NAME='${storage_name}'
  LOKOLE_EMAIL_SERVER_AZURE_BLOBS_KEY='${storage_key}'
  LOKOLE_EMAIL_SERVER_AZURE_QUEUES_KEY='${storage_key}'
  LOKOLE_EMAIL_SERVER_AZURE_TABLES_KEY='${storage_key}'
  LOKOLE_CLIENT_AZURE_STORAGE_KEY='${storage_key}'
  LOKOLE_DEFAULT_CLIENTS='[{"id":"${client_id}","domain":"${client_name}.lokole.ca"}]'
  EOF

Third, use the makefile to verify your installation by running the tests and
starting up the server. The makefile will automatically install all required
dependencies into a virtual environment.

.. sourcecode :: sh

  make tests
  make server

Alternatively, you can also run the entire application stack via Docker:

.. sourcecode :: sh

  docker-compose up --build

There are OpenAPI specifications that document the functionality of the
application and provide references to the entry points into the code
(look for "some-api-name-spec.yaml" files in the repository).
