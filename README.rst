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

  sudo apt-get install -y python3-dev python3-venv openssl-dev jq
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
  cat > .env << EOF
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

  export ENV_FILE=.env
  export BUILD_TAG=development
  export APP_PORT=8080
  docker-compose up

There is an `OpenAPI specification <https://github.com/ascoderu/opwen-cloudserver/blob/master/opwen_email_server/static/email-api-spec.yaml>`_
that documents the functionality of the application and provides pointers to the
entry points into the code. You can experiment with the endpoints in the `API test console <http://localhost:8080/api/email/ui>`_
(for any endpoints that require `client_id` to be specified, fill in the value
described in the script above, i.e., 123456789).

Production setup
----------------

First-time setup:

.. sourcecode :: sh

  location='eastus'
  name='opwenserver'
  deploy_password="FILL ME IN"
  appinsights_key="SET ME"

  # create required resources
  az group create --location="${location}" --name="${name}"
  az configure --defaults group="${name}" location="${location}"
  az storage account create --sku=standard_lrs --name="opwenserverqueues"
  az storage account create --sku=standard_lrs --name="opwenservertables"
  az storage account create --sku=standard_lrs --name="opwenserverblobs"
  az storage account create --sku=standard_lrs --name="opwenclientblobs"

  # fetch access keys
  queues_key=$(az storage account keys list --account-name="opwenserverqueues" | jq -r ".[0].value")
  tables_key=$(az storage account keys list --account-name="opwenservertables" | jq -r ".[0].value")
  blobs_key=$(az storage account keys list --account-name="opwenserverblobs" | jq -r ".[0].value")
  clients_key=$(az storage account keys list --account-name="opwenclientblobs" | jq -r ".[0].value")

  # host the app in azure
  az webapp deployment user set --user-name "${name}" --password "${deploy_password}"
  az appservice plan create --name="${name}" --sku="s1"
  az webapp create --name="${name}" --plan="${name}" --runtime="python|3.4" --deployment-local-git
  git remote add azure "https://${name}@${name}.scm.azurewebsites.net:443/${name}.git
  git push azure master

  # set environment variables
  az webapp config appsettings set --name="${name}" --settings \
    LOKOLE_EMAIL_SERVER_APPINSIGHTS_KEY="${appinsights_key}" \
    LOKOLE_EMAIL_SERVER_AZURE_QUEUES_NAME="opwenserverqueues" \
    LOKOLE_EMAIL_SERVER_AZURE_QUEUES_KEY="${queues_key}" \
    LOKOLE_EMAIL_SERVER_AZURE_TABLES_NAME="opwenservertables" \
    LOKOLE_EMAIL_SERVER_AZURE_TABLES_KEY="${tables_key}" \
    LOKOLE_EMAIL_SERVER_AZURE_BLOBS_NAME="opwenserverblobs" \
    LOKOLE_EMAIL_SERVER_AZURE_BLOBS_KEY="${blobs_key}" \
    LOKOLE_CLIENT_AZURE_STORAGE_NAME="opwenclientblobs" \
    LOKOLE_CLIENT_AZURE_STORAGE_KEY="${clients_key}"

How do I...
-----------

... test the receiving of an email from an external entity like Outlook?
````````````````````````````````````````````````````````````````````````

.. sourcecode :: sh

  # start the server and the worker that processes inbound emails
  make server &
  make inbound-store-worker &

  # simulate the Sendgrid service forwarding an email received at the Lokole MX
  # records to this service
  # the server will receive the request from Sendgrid and enqueue a message to
  # process and ingest the newly received raw MIME email
  # the inbound-store-worker then wakes up, parses the MIME email into a domain
  # object and stores it in the email datastore
  curl localhost:8080/api/email/sendgrid/YOUR_CLIENT_ID_HERE -F "email=YOUR_MIME_EMAIL_HERE"

... test the Lokole devices uploading emails written on them?
`````````````````````````````````````````````````````````````

.. sourcecode :: sh

  # start the server and the workers that process outbound emails
  make server &
  make outbound-store-worker &
  make outbound-send-worker &

  # create and upload a compressed emails package to Azure just like the Lokole
  cat "YOUR_EMAIL_DATA_HERE" > emailsFromLokole.pack
  az storage blob upload -f emailsFromLokole.pack -c compressedpackages -n test-resource-id --account-name "YOUR_ACCOUNT_NAME_HERE" --account-key "YOUR_KEY_HERE"

  # simulate the Lokole device's upload phase of the sync cycle calling out to
  # the service
  # the server will receive the Lokole's upload request and enqueue a message to
  # process and ingest the uploaded emails
  # the outbound-store-worker then wakes up, retrieves the uploaded emails from
  # Azure, stores them in the email datastore and enqueues another message to
  # send the emails to their recipients
  # the outbound-send-worker then wakes up, retrieves each email to be sent,
  # formats it into a MIME email and shoots it off to Sendgrid for delivery
  curl localhost:8080/api/email/lokole/YOUR_CLIENT_ID_HERE -X POST -d '{"resource_container":"compressedpackages","resource_id":"test-resource-id","resource_type":"azure-blob"}' -H "Content-Type: application/json"

... test the Lokole devices downloading emails sent to them?
````````````````````````````````````````````````````````````

.. sourcecode :: sh

  # start the server
  make server &

  # simulate the Lokole device's download phase of the sync cycle calling out to
  # the service
  # the server will receive the Lokole's download request, fetch all the new
  # messages sent to the Lokole device since the last request, package them and
  # upload them to Azure
  resource_id=$(curl localhost:8080/api/email/lokole/YOUR_CLIENT_ID_HERE -X GET | jq -r '.resource_id')

  # download the compressed emails package that the Lokole device would ingest
  az storage blob download -f emailsToLokole.pack -c compressedpackages -n ${resource_id} --account-name "YOUR_ACCOUNT_NAME_HERE" --account-key "YOUR_KEY_HERE"
