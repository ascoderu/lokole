Opwen webapp
============

.. image:: https://travis-ci.org/OPWEN/opwen-webapp.svg?branch=master
  :target: https://travis-ci.org/OPWEN/opwen-webapp

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
`Opwen Server <https://github.com/OPWEN/opwen-cloudserver>`_ picks up these JSON
files, manages the actual mailboxes for the users on the Lokole and sends new
emails back to the Lokole by using the same compressed file exchange format.

The Lokole web-application is intended to run on low-spec Raspberry Pi 3
hardware. There is a `script <https://github.com/OPWEN/opwen-setup>`_ to set up
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

Technical overview
------------------

Can be found in the `opwen-shared readme <https://github.com/OPWEN/opwen-shared/blob/master/README.rst>`_.

Development setup
-----------------

First, get the source code.

.. sourcecode :: sh

  git clone git@github.com:OPWEN/opwen-webapp.git

Second, install the dependencies for the package and verify your checkout by
running the tests.

.. sourcecode :: sh

  cd opwen-webapp

  virtualenv -p "$(which python3)" --no-site-packages virtualenv
  . virtualenv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt

  npm install
  bower install

  pip install nose
  nosetests

The routes of the app are defined in ``opwen_email_client/views.py`` so take
a look there for an overview of the entrypoints into the code.
