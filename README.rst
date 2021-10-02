======
Lokole
======

.. image:: https://github.com/ascoderu/lokole/workflows/CI/badge.svg
  :target: https://github.com/ascoderu/lokole/actions

.. image:: https://img.shields.io/pypi/v/opwen_email_client.svg
  :target: https://pypi.python.org/pypi/opwen_email_client/

.. image:: https://codecov.io/gh/ascoderu/lokole/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/ascoderu/lokole

------------
What's this?
------------

This repository contains the source code for the Lokole project by the
Canadian-Congolese non-profit `Ascoderu <https://ascoderu.ca>`_. The Lokole
project consists of two main parts: an email client and an email server.

The Lokole email client is a simple application that offers functionality like:

1. Self-service creation of user accounts
2. Read emails sent to the account
3. Write emails including rich formatting
4. Send attachments

All emails are stored in a local SQLite database. Once per day, the emails that
were written during the past 24 hours get exported from the database, stored in
a JSON file, compressed and uploaded to a location on Azure Blob Storage. The
Lokole Server picks up these JSON files, manages the actual mailboxes for the
users on the Lokole and sends new emails back to the Lokole by using the same
compressed file exchange format.

The Lokole email application is intended to run on low-spec Raspberry Pi 3
hardware (or similar). Read the "Production setup" section below for further
information on how to set up the client devices.

The Lokole email server has two main responsibilities:

1. Receive emails from the internet that are addressed to Lokole users and
   forward them to the appropriate Lokole device.
2. Send new emails created by Lokole users to the rest of the internet.

-------------------
Why is this useful?
-------------------

Email is at the core of our modern life, letting us keep in touch with friends
and family, connecting us to our businesses partners and fostering innovation
through exchange of information.

However, in many parts of the developing world, email access is not very
wide-spread, usually because bandwidth costs are prohibitively high compared to
local purchasing power. For example, in the Democratic Republic of the Congo
(DRC) only 3% of the population have access to emails which leaves 75 million
people unconnected.

The Lokole is a project by the Canadian-Congolese non-profit `Ascoderu <https://ascoderu.ca>`_
that aims to address this problem by tackling it from three perspectives:

1. The Lokole is an email client that only uses bandwidth on a schedule. This
   reduces the cost of service as bandwidth can now be purchased when the cost
   is lowest. For example, in the DRC, $1 purchases only 65 MB of data during
   peak hours. At night, however, the same amount of money buys 1 GB of data.

2. The Lokole uses an efficient data exchange format plus compression so that
   it uses minimal amounts of bandwidth, reducing the cost of service. All
   expensive operations (e.g. creating and sending of emails with headers,
   managing mailboxes, etc.) are performed on a server in a country where
   bandwidth is cheap.

3. The Lokole only uses bandwidth in batches. This means that the cost of
   service can be spread over many people and higher savings from increased
   compression ratios can be achieved. For example, individually purchasing
   bandwidth for $1 to check emails is economically un-viable for most people
   in the DRC. However, the same $1 can buy enough bandwidth to provide email
   for hundreds of people via the Lokole. Spreading the cost in this way makes
   email access sustainable for local communities.

---------------
System overview
---------------

Technologies
============

Below is a list of some of the key technologies used in the Lokole project:

- `Connexion <https://jobs.zalando.com/tech/blog/crafting-effective-microservices-in-python/>`_ is the web framework for the Lokole email server API.
- `Flask <https://flask.palletsprojects.com/>`_ is the web framework for the Lokole email client application.
- `Dnsmasq <http://www.thekelleys.org.uk/dnsmasq/doc.html>`_ and `hostapd <https://w1.fi/hostapd/>`_ are used to set up a WiFi access point on the Lokole device via which the Lokole email client application is accessed.
- `WvDial <https://wiki.debian.org/Wvdial>`_ is used to access the internet on the Lokole device to synchronize emails with the Lokole email server.
- `Celery <http://www.celeryproject.org/>`_ is used to run background workers of the Lokole email server in `Azure ServiceBus <https://azure.microsoft.com/en-us/services/service-bus/>`_ (production) or `RabbitMQ <https://www.rabbitmq.com/>`_ (development). Celery is also used to run background workers and scheduled tasks on the Lokole email client application in `SQLAlchemy <https://www.sqlalchemy.org/>`_.
- `Libcloud <https://libcloud.apache.org/>`_ is used to store emails in `Azure Storage <https://azure.microsoft.com/en-us/services/storage/>`_ (production) or `Azurite <https://github.com/Azure/Azurite>`_ (development).
- `Sendgrid Inbound Parse <https://sendgrid.com/docs/for-developers/parsing-email/setting-up-the-inbound-parse-webhook/>`_ is used to receive emails from email providers and forward them to the Lokole email server. `Sendgrid Web API v3 <https://github.com/sendgrid/sendgrid-python>`_ is used to deliver emails from the Lokole email server to email providers. The MX records for Sendgrid are automatically generated via `Cloudflare API v4 <https://api.cloudflare.com/>`_.
- `Github API v4 <https://developer.github.com/v4/>`_ is used to authenticate interactive calls to the Lokole email server API such as registering new clients or managing existing clients. Authorization is managed by Github team memberships on the Ascoderu organization. Management operations are exposed via the Lokole status page which is implemented in `React <https://reactjs.org/>`_ with `Ant Design <https://ant.design/docs/react/introduce>`_.
- `Github Actions <https://github.com/ascoderu/lokole/actions>`_ are used to verify pull requests and deploy updates to production.

The diagram below shows the technologies in the context of the system as well as their interactions:

.. image:: https://user-images.githubusercontent.com/1086421/95025387-687ee480-0657-11eb-8519-4ef4c0224648.png
  :width: 800
  :align: center
  :alt: Overview of technologies and interactions in the Lokole system
  :target: https://drive.google.com/file/d/1F9LMqpoglaKWRw8HjhZ1jzPkdCMpuOur/view

Interactions
============

The key data flows and client/server interactions of the system are documented in the diagrams below.

.. image:: https://static.swimlanes.io/23added12f9ab7faa03ac6d1c6bdc733.png
  :width: 800
  :align: center
  :alt: Overview of the Lokole client registration flow
  :target: https://swimlanes.io/u/SfWS0LVYu

.. image:: https://static.swimlanes.io/b070c40083a3f67ede3e49fa9cd25933.png
  :width: 800
  :align: center
  :alt: Overview of the Lokole client email upload flow
  :target: https://swimlanes.io/u/hub7TEZgp

.. image:: https://static.swimlanes.io/3dc4b74d377eb3094dc83fc1da9dfe84.png
  :width: 800
  :align: center
  :alt: Overview of the Lokole client email download flow
  :target: https://swimlanes.io/u/_QqT0iQx8

--------------------
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
    "attachments": [{"filename": "string", "content": "base64", "cid": "string"}]
  }

-----------------
Development setup
-----------------

First, install the system dependencies:

- `docker <https://docs.docker.com>`_
- `docker-compose <https://docs.docker.com/compose/>`_
- `git <https://git-scm.com>`_
- `make <https://www.gnu.org/software/make/>`_

Second, get the source code.

.. sourcecode :: sh

  git clone git@github.com:ascoderu/lokole.git
  cd lokole

Third, build the project images. This will also verify your checkout by
running the unit tests and other CI steps such as linting:

.. sourcecode :: sh

  make build

You can now run the application stack:

.. sourcecode :: sh

  make start logs

Finding your way around the project
===================================

There are OpenAPI specifications that document the functionality of the
application and provide references to the entry points into the code
(look for the yaml files in the swagger directory). The various
APIs can also be easily called via the testing console that is available
by adding /ui to the end of the API's URL. Sample workflows are shown
in the integration tests folder and can be run via:

.. sourcecode :: sh

  # run the services, wait for them to start
  make build start

  # in another terminal, run the integration tests
  # the integration tests also serve the purpose of
  # seeding the system with some test data
  # you can access the email service at http://localhost:8080
  # you can access the email client at http://localhost:5000
  # you can access the status page at http://localhost:3000
  make integration-tests test-emails

  # finally, tear down the services
  make stop

The state of the system can be inspected via:

.. sourcecode :: sh

  # run the development tools and then
  # view storage state at http://localhost:10001
  # view database state at http://localhost:8882
  # view queue state at http://localhost:5555
  make start-devtools

Note that by default the application is run in a fully local mode, without
leveraging any cloud services. For most development purposes this is fine
but if you wish to set up the full end-to-end stack that leverages the
same services as we use in production, keep on reading.

Integration setup
=================

The project uses Sendgrid, so to emulate a full production environment,
follow these `Sendgrid setup instructions <https://sendgrid.com/free/>`_ to
create a free account, authenticate your domain, and create an API key with
at least Inbound Parse and Mail Send permissions.

The project uses Cloudflare to automate DNS management whenever new Lokole
clients are set up. Create an account, set your domain to be managed by
Cloudflare and look up the `Cloudflare Global API Key <https://dash.cloudflare.com/profile/api-tokens>`_.

The project also makes use of a number of Azure services such as Blobs,
Tables, Queues, Application Insights, and so forth. To set up all the
required cloud resources programmatically, you'll need to create a service
principal by following these `Service Principal instructions <https://aka.ms/create-sp>`_.
After you created the service principal, you can run the Docker setup script
to initialize the required cloud resources.

.. sourcecode :: sh

  cat > ${PWD}/secrets/sendgrid.env << EOM
  LOKOLE_SENDGRID_KEY={the sendgrid key you created earlier}
  EOM

  cat > ${PWD}/secrets/cloudflare.env << EOM
  LOKOLE_CLOUDFLARE_USER={your cloudflare user account email address}
  LOKOLE_CLOUDFLARE_KEY={your cloudflare global api key}
  EOM

  cat > ${PWD}/secrets/users.env << EOM
  OPWEN_SESSION_KEY={some secret for user session management}
  LOKOLE_REGISTRATION_USERNAME={some username for the registration endpoint}
  LOKOLE_REGISTRATION_PASSWORD={some password for the registration endpoint}
  EOM

  docker-compose -f ./docker-compose.yml -f ./docker/docker-compose.setup.yml build setup
  docker-compose -f ./docker-compose.yml -f ./docker/docker-compose.setup.yml run --rm \
    -e SP_APPID={appId field of your service principal} \
    -e SP_PASSWORD={password field of your service principal} \
    -e SP_TENANT={tenant field of your service principal} \
    -e SUBSCRIPTION_ID={subscription id of your service principal} \
    -e LOCATION={an azure location like eastus} \
    -e RESOURCE_GROUP_NAME={the name of the resource group to create or reuse} \
    -v ${PWD}/secrets:/secrets \
    setup ./setup.sh

The secrets to access the Azure resources created by the setup script will be
stored in files in the :code:`secrets` directory. Other parts of the
project's tooling (e.g. docker-compose) depend on these files so make sure to
not delete them.

---------------------
Production deployment
---------------------

To set up a production-ready deployment of the system, follow the development
setup scripts described above, but additionally also pass the following
environment variables to the Docker setup script:

- :code:`DEPLOY_COMPUTE`: Must be set to :code:`k8s` to toggle the Kubernetes
  deployment mode.

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

As an alternative to the Kubnernets deployment, a Virtual Machine may also be
provisioned to run the services by passing the following environment variables
to the Docker setup script:

- :code:`DEPLOY_COMPUTE`: Must be set to :code:`vm` to toggle the Virtual
  Machine deployment mode.

- :code:`VM_RESOURCE_GROUP_NAME`: The resource group into which to
  provision the Azure Virtual Machine.

- :code:`VM_SKU`: The type of VMs to provision into the cluster.
  This should be one of the supported `Linux VM sizes <https://docs.microsoft.com/en-us/azure/virtual-machines/linux/sizes>`_.

There is a `script <https://github.com/ascoderu/lokole/blob/master/install.py>`_
to set up a new Lokole email client. The script will install the email app in this
repository as well as standard infrastructure like nginx and gunicorn.
The script will also make ready peripherals like the USB modem used for data
exchange, and set up any required background jobs such as the email
synchronization cron job.

The setup script assumes that you have already set up:

* 3 Azure Storage Accounts, general purpose: for the cloudserver to manage its
  queues, tables and blobs.
* 1 Azure Storage Account, blob storage: for the cloudserver and email app to
  exchange email packages.
* 1 Application Insights account: to collect logs from the cloudserver and
  monitor its operations.
* 1 SendGrid account: to send and receive emails in the cloudserver.

The setup script is tested with hardware:

* `Raspberry Pi 3 <https://www.raspberrypi.org/products/raspberry-pi-3-model-b/>`_
  running Raspbian Jessie lite
  `v2016-05-27 <https://downloads.raspberrypi.org/raspbian_lite/images/raspbian_lite-2016-05-31/2016-05-27-raspbian-jessie-lite.zip>`_,
  `v2017-01-11 <https://downloads.raspberrypi.org/raspbian_lite/images/raspbian_lite-2017-01-10/2017-01-11-raspbian-jessie-lite.zip>`_,
  `v2017-04-10 <https://downloads.raspberrypi.org/raspbian_lite/images/raspbian_lite-2017-04-10/2017-04-10-raspbian-jessie-lite.zip>`_, and
  `v2017-11-29 <http://vx2-downloads.raspberrypi.org/raspbian_lite/images/raspbian_lite-2017-12-01/2017-11-29-raspbian-stretch-lite.zip>`_.

* `Orange Pi Zero <http://www.orangepi.org/orangepizero/>`_
  running `Armbian Ubuntu Xenial <https://dl.armbian.com/orangepizero/Ubuntu_xenial_default.7z>`_

The setup script is also tested with USB modems:

* `Huawei E303s-65 <https://www.aliexpress.com/item/4000961436981.html>`_
* `Huawei E3131 <https://www.aliexpress.com/item/32404274659.html>`_
* `Huawei MS2131i-8 <https://www.aliexpress.com/item/32964337576.html>`_

The setup script installs the latest version of the email app published to PyPI.
New versions get automatically published to PyPI (via Travis) whenever a new
`release <https://github.com/ascoderu/lokole/releases/new>`_ is created
on Github.

You can run the script on your client device like so:

.. sourcecode :: sh

  curl -fsO https://raw.githubusercontent.com/ascoderu/lokole/master/install.py && \
  sudo python3 install.py <client-name> <sim-type> <sync-schedule> <registration-credentials>

---------------------
Adding a new language
---------------------

To translate Lokole to a new language, install Python, `Babel <https://babel.pocoo.org/>`_
and a translation editor such as `poedit <https://poedit.net/>`_. Then follow the steps below.

.. sourcecode :: sh

  # set this to the ISO 639-1 language code for which you are adding the translation
  export language=ln

  # generate the translation file
  pybabel init -i babel.pot -d opwen_email_client/webapp/translations -l "${language}"

  # fill-in the translation file
  poedit "opwen_email_client/webapp/translations/${language}/LC_MESSAGES/messages.po"

  # finalize the translation file
  pybabel compile -d opwen_email_client/webapp/translations
