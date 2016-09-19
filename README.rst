Opwen webapp
============

.. image:: https://travis-ci.org/OPWEN/opwen-webapp.svg?branch=master
  :target: https://travis-ci.org/OPWEN/opwen-webapp

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

Data exchange format
--------------------

In order to communicate between the Opwen server and the Lokole a protocol based
on zip archives uploaded to Azure Blob Storage is used.

There are two locations on Azure Blob Storage where these archives can be found.

- The Opwen server will expect the new emails from the Lokole to be uploaded to:

  ``{blob-root}/{lokole-name}/from_opwen/{year-month-day_hour-minute}.zip``

- The Lokole will expect new emails from the Opwen server to be uploaded to:

  ``{blob-root}/{lokole-name}/to_opwen/new.zip``

The archive contains the files described in the following sections.

emails.jsonl
~~~~~~~~~~~~

This file contains a JSON object per line. Each JSON object describes an email.

.. sourcecode :: json

  {
    "date": "year-month-day hour:minute",
    "to": ["email"],
    "from": "lokole-user|email",
    "subject": "str",
    "message": "html",
    "attachments": [{"filename": "str", "relativepath": "path/to/file"}]
  }

Description of fields:

- *date* encodes the time at which the email was sent, in UTC.

- *to* stores the email address to which the email is sent.

- *from* is the sender of the email. If the email was sent from a Lokole account
  that isn't associated with an email address yet, the account's user name is
  put in the field instead. In this case, the Lokole will expect the Opwen
  server to create a new email account for the Lokole account and communicate
  back the email address now associated with the Lokole account via the
  ``accounts.jsonl`` file described below.

- *subject* encodes the subject of the email as a plain unicode string.

- *message* stores the content of the email, as a html-formatted unicode string.

- *attachments* is an optional field that contains the attachments (if any)
  associated with the email. Each JSON object in this list describes one
  attachment. The *filename* field is the name of the file that the user
  attached to the email. The *relativepath* field is the full path in the zip
  archive including file name where the attachment can be found. Note that most
  of the time the name of the file that the user attached to the email and the
  name of the file included in the zip archive will not be the same because
  attachments get renamed to a content-hash before being included in the zip
  archive. This is done so that multiple emails that share the same attachments
  don't lead to redundant information being transmitted in the zip archive.

accounts.jsonl
~~~~~~~~~~~~~~

This file contains a JSON object per line. Each JSON object describes a fully
fledged Lokole account.

.. sourcecode :: json

  {
    "name": "lokole-user",
    "email": "email"
  }

Description of fields:

- *name* encodes the name of the Lokole account that was completed by the Opwen
  server.

- *email* is the newly created email address that is now associated with the
  Lokole account. This will be persisted in the local database on the Lokole.

Development setup
-----------------

First, get the source code.

.. sourcecode :: sh

  git clone git@github.com:OPWEN/opwen-webapp.git

Second, install the dependencies for the package and verify your checkout by
running the tests.

.. sourcecode :: sh

  cd opwen-webapp

  virtualenv -p $(which python3) --no-site-packages virtualenv
  . virtualenv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  bower install

  pip install nose
  nosetests

Third, create your local database for development and seed it with some random
test data.

.. sourcecode :: sh

  touch opwen.db
  ./manage.py db upgrade
  ./manage.py db migrate
  ./manage.py dbpopulate
