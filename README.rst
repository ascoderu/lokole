Opwen webapp
============

.. image:: https://travis-ci.org/ascoderu/opwen-webapp.svg?branch=master
  :target: https://travis-ci.org/ascoderu/opwen-webapp

.. image:: https://img.shields.io/pypi/v/opwen_email_client.svg
  :target: https://pypi.python.org/pypi/opwen_email_client/

.. image:: https://pyup.io/repos/github/ascoderu/opwen-webapp/shield.svg
  :target: https://pyup.io/repos/github/ascoderu/opwen-webapp/

.. image:: https://codecov.io/gh/ascoderu/opwen-webapp/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/ascoderu/opwen-webapp

What's this?
------------

This repository contains the source code for the Lokole email application.
Lokole is a project by the Canadian-Congolese non-profit `Ascoderu <https://ascoderu.ca>`_.

The Lokole is a simple email client that offers functionality like:

1. Self-service creation of user accounts
2. Read emails sent to the account
3. Write emails including rich formatting
4. Send attachments

All emails are stored in a local SQLite database. Once per day, the emails that
were written during the past 24 hours get exported from the database, stored in
a JSON file, compressed and uploaded to a location on Azure Blob Storage. The
`Lokole Server <https://github.com/ascoderu/opwen-cloudserver>`_ picks up these
JSON files, manages the actual mailboxes for the users on the Lokole and sends
new emails back to the Lokole by using the same compressed file exchange format.

The Lokole email application is intended to run on low-spec Raspberry Pi 3
hardware (or similar). Read the "Production setup" section below for further
information on how to set up the client devices.

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

System overview & Data exchange format
--------------------------------------

Can be found in the `opwen-cloudserver README <https://github.com/ascoderu/opwen-cloudserver/blob/master/README.rst>`_.

Development setup
-----------------

First, get the source code.

.. sourcecode :: sh

  git clone https://github.com/ascoderu/opwen-webapp.git
  cd opwen-webapp

Second, install the system-level dependencies using your package manager,
e.g. on Ubuntu:

.. sourcecode :: sh

  curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
  echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
  sudo apt-get update
  sudo apt-get install -y yarn make python3 python3-venv

Third, use the makefile to verify your installation by running the tests and
starting up the server. The makefile will automatically install all required
dependencies into a virtual environment and set up some dummy environment
variables for local development. The server will automatically reload whenever
any of the Flask code or Jinja templates are changed.

.. sourcecode :: sh

  make tests
  make server
  make worker

The routes of the app are defined in `views.py <https://github.com/ascoderu/opwen-webapp/blob/master/opwen_email_client/webapp/views.py>`_
so take a look there for an overview of the entrypoints into the code.

When the Lokole exchanges data with the server, it will not make any calls to Azure
and instead depend on the files in the `./tests/files/opwen_email_client` directory.
Any files uploaded to the server will be written to the `compressedpackages`
subdirectory so that they can be inspected. To test sending emails from the server
to the Lokole, a sample email batch file is included in the `compressedpackages`
directory. This file will be ingested by the client when the `/admin/sync` endpoint
is called.

Production setup
----------------

There is a `script <https://github.com/ascoderu/opwen-webapp/blob/master/install.py>`_
to set up a new Lokole device. The script will install the email app in this
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

* `Huawei E303s-65 <http://consumer.huawei.com/cl/mobile-broadband/dongles/tech-specs/e303-cl.htm>`_
* `Huawei E3131 <http://consumer.huawei.com/lk/mobile-broadband/dongles/tech-specs/e3131-lk.htm>`_
* `Huawei MS2131i-8 <http://consumer.huawei.com/en/solutions/m2m-solutions/products/tech-specs/ms2131-en.htm>`_

The setup script installs the latest version of the email app published to PyPI.
New versions get automatically published to PyPI (via Travis) whenever a new
`release <https://github.com/ascoderu/opwen-webapp/releases/new>`_ is created
on Github.

You can run the script on your client device like so:

.. sourcecode :: sh

  curl -fsO https://raw.githubusercontent.com/ascoderu/opwen-webapp/master/install.py && \
  sudo python3 install.py <client-name> <sim-type> <sync-schedule> <registration-credentials>


Adding a new language
---------------------

.. sourcecode :: sh

  export LANG=ln
  make prepare-translations
  poedit "opwen_email_client/webapp/translations/$LANG/LC_MESSAGES/messages.po"
  make compile-translations

Or via `Transifex <https://www.transifex.com/ascoderu/opwen-webapp/dashboard/>`_.
