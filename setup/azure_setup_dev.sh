#!/usr/bin/env bash

azure_subscription_id="$1"

if [ -z "${azure_subscription_id}" ]; then
  echo "Usage: $0 <azure_subscription_id>" >&2
  exit 1
fi

#
# connect to Azure account
#
az login
az account set --subscription "${azure_subscription_id}"

#
# define client properties
#
client_name="$(whoami | tr -dC 'a-zA-Z0-9')"
client_id="123456789"

#
# create development Azure resources
#
location="eastus"
resource_group="opwentest${client_name}"
storage_name="opwenteststorage${client_name}"
az group create -n "${resource_group}" -l "${location}"
az storage account create -n "${storage_name}" -g "${resource_group}" -l "${location}" --sku Standard_RAGRS

#
# setup environment variables
#
storage_key="$(az storage account keys list -n "${storage_name}" -g "${resource_group}" | jq -r '.[0].value')"

cat > "$(dirname "$0")/../secrets.env" << EOF
LOKOLE_EMAIL_SERVER_AZURE_BLOBS_NAME=${storage_name}
LOKOLE_EMAIL_SERVER_AZURE_QUEUES_NAME=${storage_name}
LOKOLE_EMAIL_SERVER_AZURE_TABLES_NAME=${storage_name}
LOKOLE_CLIENT_AZURE_STORAGE_NAME=${storage_name}
LOKOLE_EMAIL_SERVER_AZURE_BLOBS_KEY=${storage_key}
LOKOLE_EMAIL_SERVER_AZURE_QUEUES_KEY=${storage_key}
LOKOLE_EMAIL_SERVER_AZURE_TABLES_KEY=${storage_key}
LOKOLE_CLIENT_AZURE_STORAGE_KEY=${storage_key}
LOKOLE_DEFAULT_CLIENTS=[{"id":"${client_id}","domain":"${client_name}.lokole.ca"}]
EOF
