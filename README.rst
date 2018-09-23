Opwen cloudserver
=================

.. image:: https://travis-ci.org/ascoderu/opwen-cloudserver.svg?branch=master
  :target: https://travis-ci.org/ascoderu/opwen-cloudserver

.. image:: https://img.shields.io/pypi/v/opwen_email_server.svg
  :target: https://pypi.python.org/pypi/opwen_email_server/

.. image:: https://pyup.io/repos/github/ascoderu/opwen-cloudserver/shield.svg
  :target: https://pyup.io/repos/github/ascoderu/opwen-cloudserver/

.. image:: https://codecov.io/gh/ascoderu/opwen-cloudserver/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/ascoderu/opwen-cloudserver

What's this?
------------

This repository contains the source code for the Lokole cloud server. Its
purpose is to connect the `application <https://github.com/ascoderu/opwen-webapp>`_
running on the Lokole devices to the rest of the world. Lokole is a project
by the Canadian-Congolese non-profit `Ascoderu <https://ascoderu.ca>`_.

The server is implemented using `Connexion <https://jobs.zalando.com/tech/blog/crafting-effective-microservices-in-python/>`_
and has two main responsibilities:

1. Receive emails from the internet that are addressed to Lokole users and
   forward them to the appropriate Lokole device.
2. Send new emails created by Lokole users to the rest of the internet.

More background information can be found in the `opwen-webapp README <https://github.com/ascoderu/opwen-webapp/blob/master/README.rst>`_.

System overview
---------------

.. image:: https://user-images.githubusercontent.com/1086421/42739204-67798f44-8847-11e8-9613-312a860cfb1e.png
  :width: 800
  :align: center
  :alt: Overview of the Lokole system
  :target: https://user-images.githubusercontent.com/1086421/42739204-67798f44-8847-11e8-9613-312a860cfb1e.png

Data exchange format
--------------------

In order to communicate between the Lokole cloud server and the Lokole email
application, a protocol based on gzipped jsonl files uploaded to Azure Blob
Storage is used. The files contains a JSON object per line. Each JSON object
describes an email, using the following schema:

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

Second, install the system-level dependencies using your package manager,
e.g. on Ubuntu:

.. sourcecode :: sh

  sudo apt-get install -y make python3-venv shellcheck

You can use the makefile to verify your checkout by running the tests and
other CI steps such as linting. The makefile will automatically install all
required dependencies into a virtual environment.

.. sourcecode :: sh

  make tests
  make lint

This project consists of a number of microservices and background jobs. You
can run all the pieces via the makefile, however, it's easiest to run and
manage all of the moving pieces via Docker, so install Docker on your machine
by following the `Docker setup instructions <https://docs.docker.com/install/>`_
for your platform.

The project uses Sendgrid, so to emulate a full production environment,
follow these `Sendgrid setup instructions <https://sendgrid.com/free/>`_ to
create a free account and take note of you API key for sending emails.

The project also makes use of a number of Azure services such as Blobs,
Tables, Queues, Application Insights, and so forth. To set up all the
required cloud resources programmatically, you'll need to create a service
principal by following these `Service Principal instructions <https://aka.ms/create-sp>`_.
After you created the service principal, you can run the Docker setup script
to initialize the required cloud resources.

.. sourcecode :: sh

  docker build -t setup -f docker/setup/Dockerfile .

  docker run \
    -e SP_APPID={appId field of your service principal} \
    -e SP_PASSWORD={password field of your service principal} \
    -e SP_TENANT={tenant field of your service principal} \
    -e SUBSCRIPTION_ID={subscription id of your service principal} \
    -e LOCATION={an azure location like eastus} \
    -e RESOURCE_GROUP_NAME={the name of the resource group to create or reuse} \
    -e SENDGRID_KEY={the sendgrid key you created earlier} \
    -v ${PWD}/secrets:/secrets \
    setup

The secrets to access the Azure resources created by the setup script will be
stored in files in the :code:`secrets` directory. Other parts of the
project's tooling (e.g. docker-compose) depend on these files so make sure to
not delete them.

Finall, run the application stack via Docker:

.. sourcecode :: sh

  docker-compose up --build

There are OpenAPI specifications that document the functionality of the
application and provide references to the entry points into the code
(look for "some-api-name-spec.yaml" files in the repository).

Production setup
----------------

To set up a production-ready deployment of the system, follow the development
setup scripts described above, but additionally also pass the following
environment variables to the Docker setup script:

- :code:`KUBERNETES_RESOURCE_GROUP_NAME`: The resource group into which to
  provision the Azure Kubernetes Service cluster.

- :code:`KUBERNETES_NODE_COUNT`: The number of VMs to provision into the
  cluster. This should be an odd number and can be dynamically changed later
  via the Azure CLI.

- :code:`KUBERNETES_NODE_SKU`: The type of VMs to provision into the cluster.
  This should be one of the supported `Linux VM sizes <https://docs.microsoft.com/en-us/azure/virtual-machines/linux/sizes>`_.

The script will then provision a cluster in Azure Kubernetes Service and
install the project via Helm. The secrets to connect to the provisioned
cluster will be stored in the :code:`secrets` directory.
