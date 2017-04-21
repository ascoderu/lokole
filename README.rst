Opwen webapp
============

.. image:: https://travis-ci.org/ascoderu/opwen-webapp.svg?branch=master
  :target: https://travis-ci.org/ascoderu/opwen-webapp

.. image:: https://img.shields.io/pypi/v/opwen_email_client.svg
  :target: https://pypi.python.org/pypi/opwen_email_client/

What's this?
------------

This repository contains the source code for the Opwen Lokole web-application.

The Lokole is a simple email client that has functionality like:

1. Self-service creation of user accounts
2. Read emails sent to the account
3. Write emails including rich formatting
4. Send attachments

All emails are stored in a local SQLite database. Once per day, the emails that
were written during the past 24 hours get exported from the database, stored in
a JSON file, compressed and uploaded to a location on Azure Blob Storage. The
`Opwen Server <https://github.com/ascoderu/opwen-cloudserver>`_ picks up these JSON
files, manages the actual mailboxes for the users on the Lokole and sends new
emails back to the Lokole by using the same compressed file exchange format.

The Lokole web-application is intended to run on low-spec Raspberry Pi 3
hardware. There is a `script <https://github.com/ascoderu/opwen-setup>`_ to set up
the hardware with all the bits and pieces necessary to run the Lokole
web-application: web server, wsgi server, etc.

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

The Opwen Lokole is a project by the Canadian-Congolese NGO Ascoderu that aims
to address this problem by tackling it from three perspectives:

1. The Lokole is an email client that only uses bandwidth on a schedule. This
   reduces the cost of service as bandwidth can now be purchased when the cost
   is lowest. For example, in the DRC, $1 purchases only 65 MB of data during
   peak hours. At night, however, the same amount of money buys 1 GB of data.

2. The Lokole uses an efficient data exchange format plus compression so that it
   uses minimal amounts of bandwidth, reducing the cost of service. All
   expensive operations (e.g. creating and sending of emails with headers,
   managing mailboxes, etc.) are performed on a server in a country where
   bandwidth is cheap.

3. The Lokole only uses bandwidth in batches. This means that the cost of
   service can be spread over many people and higher savings from increased
   compression ratios can be achieved. For example, individually purchasing
   bandwidth for $1 to check emails is economically un-viable for most people in
   the DRC. However, the same $1 can buy enough bandwidth to provide email for
   hundreds of people via the Lokole. Spreading the cost in this way makes
   email access sustainable for local communities.

System overview & Data exchange format
--------------------------------------

Can be found in the `opwen-cloudserver readme <https://github.com/ascoderu/opwen-cloudserver/blob/master/README.rst>`_.

Development setup
-----------------

First, get the source code.

.. sourcecode :: sh

  git clone git@github.com:ascoderu/opwen-webapp.git

Second, install the system-level dependencies using your package manager.

.. sourcecode :: sh

  sudo dnf install npm

Third, use the makefile to verify your installation by running the tests and
starting up the server. The makefile will automatically install all required
dependencies into a virtual environment.

.. sourcecode :: sh

  cd opwen-webapp

  make tests
  make build-js
  make server

The routes of the app are defined in `views.py <https://github.com/ascoderu/opwen-webapp/blob/master/opwen_email_client/webapp/views.py>`_
so take a look there for an overview of the entrypoints into the code.
