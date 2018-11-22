#!/usr/bin/env bash
##
## This script sets up all the required Azure resources for the
## opwen-cloudserver project. The script stores the secrets to
## access the created resources in the folder /secrets as dotenv files.
##
## Required environment variables:
##
##   SP_APPID
##   SP_PASSWORD
##   SP_TENANT
##   SUBSCRIPTION_ID
##   LOCATION
##   RESOURCE_GROUP_NAME
##
## Optional environment variables:
##
##   SERVICE_BUS_SKU
##   STORAGE_ACCOUNT_SKU
##
##   KUBERNETES_RESOURCE_GROUP_NAME
##   KUBERNETES_IMAGE_REGISTRY
##   KUBERNETES_DOCKER_TAG
##   KUBERNETES_NODE_SKU
##   KUBERNETES_NODE_COUNT
##

scriptdir="$(dirname "$0")"
scriptname="${BASH_SOURCE[0]}"
. "${scriptdir}/utils.sh"

#
# verify inputs
#

required_env "${scriptname}" "SP_APPID"
required_env "${scriptname}" "SP_PASSWORD"
required_env "${scriptname}" "SP_TENANT"
required_env "${scriptname}" "SUBSCRIPTION_ID"
required_env "${scriptname}" "LOCATION"
required_env "${scriptname}" "RESOURCE_GROUP_NAME"

#
# connect to azure
#

log "Connecting to Azure"
az login --service-principal -u "${SP_APPID}" -p "${SP_PASSWORD}" -t "${SP_TENANT}"
az account set --subscription "${SUBSCRIPTION_ID}"
az configure --defaults location="${LOCATION}"

#
# setup resource group
#

use_resource_group "${RESOURCE_GROUP_NAME}"

#
# setup azure resources
#

storageaccountsku="${STORAGE_ACCOUNT_SKU:-Standard_GRS}"
servicebussku="${SERVICE_BUS_SKU:-Basic}"
deploymentname="opwendeployment$(generate_identifier 8)"

log "Creating resources via deployment ${deploymentname}"

az group deployment create \
  --name "${deploymentname}" \
  --template-file "${scriptdir}/arm.template.json" \
  --parameters storageAccountSKU="${storageaccountsku}" \
  --parameters serviceBusSKU="${servicebussku}" \
> /tmp/deployment.json

cat > /secrets/azure.env << EOF
RESOURCE_GROUP=${RESOURCE_GROUP_NAME}
LOKOLE_EMAIL_SERVER_APPINSIGHTS_KEY=$(jq -r .properties.outputs.appinsightsKey.value /tmp/deployment.json)
LOKOLE_CLIENT_AZURE_STORAGE_KEY=$(jq -r .properties.outputs.clientBlobsKey.value /tmp/deployment.json)
LOKOLE_CLIENT_AZURE_STORAGE_NAME=$(jq -r .properties.outputs.clientBlobsName.value /tmp/deployment.json)
LOKOLE_EMAIL_SERVER_AZURE_BLOBS_KEY=$(jq -r .properties.outputs.serverBlobsKey.value /tmp/deployment.json)
LOKOLE_EMAIL_SERVER_AZURE_BLOBS_NAME=$(jq -r .properties.outputs.serverBlobsName.value /tmp/deployment.json)
LOKOLE_EMAIL_SERVER_AZURE_TABLES_KEY=$(jq -r .properties.outputs.serverTablesKey.value /tmp/deployment.json)
LOKOLE_EMAIL_SERVER_AZURE_TABLES_NAME=$(jq -r .properties.outputs.serverTablesName.value /tmp/deployment.json)
LOKOLE_EMAIL_SERVER_QUEUES_NAMESPACE=$(jq -r .properties.outputs.serverQueuesName.value /tmp/deployment.json)
LOKOLE_EMAIL_SERVER_QUEUES_SAS_NAME=$(jq -r .properties.outputs.serverQueuesSasName.value /tmp/deployment.json)
LOKOLE_EMAIL_SERVER_QUEUES_SAS_KEY=$(jq -r .properties.outputs.serverQueuesSasKey.value /tmp/deployment.json)
EOF

#
# create production deployment
#

if [[ -z "${KUBERNETES_RESOURCE_GROUP_NAME}" ]] || [[ -z "${KUBERNETES_NODE_COUNT}" ]] || [[ -z "${KUBERNETES_NODE_SKU}" ]]; then
  log "Skipping production deployment to kubernetes since KUBERNETES_RESOURCE_GROUP_NAME, KUBERNETES_NODE_COUNT, or KUBERNETES_NODE_SKU are not set"
  exit 0
fi

k8sname="opwencluster$(generate_identifier 8)"
helmname="opwenserver$(generate_identifier 8)"

log "Creating kubernetes cluster ${k8sname}"

use_resource_group "${KUBERNETES_RESOURCE_GROUP_NAME}"

az provider register --wait --namespace Microsoft.Network
az provider register --wait --namespace Microsoft.Storage
az provider register --wait --namespace Microsoft.Compute
az provider register --wait --namespace Microsoft.ContainerService

az aks create \
  --service-principal "${SP_APPID}" \
  --client-secret "${SP_PASSWORD}" \
  --name "${k8sname}" \
  --node-count "${KUBERNETES_NODE_COUNT}" \
  --node-vm-size "${KUBERNETES_NODE_SKU}" \
  --generate-ssh-keys

az aks get-credentials --name "${k8sname}"

log "Setting up kubernetes secrets for ${k8sname}"

kubectl create secret generic "azure" --from-env-file "/secrets/azure.env"
kubectl create secret generic "cloudflare" --from-env-file "/secrets/cloudflare.env"
kubectl create secret generic "nginx" --from-env-file "/secrets/nginx.env"
kubectl create secret generic "sendgrid" --from-env-file "/secrets/sendgrid.env"

log "Setting up helm chart in cluster ${k8sname}"

helm init --wait

k8simageregistry="${KUBERNETES_IMAGE_REGISTRY:-cwolff}"
k8sdockertag="${KUBERNETES_DOCKER_TAG:-latest}"

while :; do
  helm install \
    --name "${helmname}" \
    --set version.imageRegistry="${k8simageregistry}" \
    --set version.dockerTag="${k8sdockertag}" \
    "${scriptdir}/helm"

  if [[ "$?" -ne 0 ]]; then log "Intermittent error for ${helmname}"; sleep 30s; else break; fi
done

while :; do
  ingressip="$(kubectl get service --selector io.kompose.service=nginx --output jsonpath={..ip})"
  if [[ -z "${ingressip}" ]]; then log "Waiting for ${k8sname} public IP"; sleep 30s; else break; fi
done

cp ~/.kube/config /secrets/kube-config
cp ~/.ssh/id_rsa.pub /secrets/kube-id_rsa.pub
cp ~/.ssh/id_rsa /secrets/kube-id_rsa

cat > /secrets/kubedeployment.env << EOF
RESOURCE_GROUP=${KUBERNETES_RESOURCE_GROUP_NAME}
HELM_NAME=${helmname}
APP_IP=${ingressip}
EOF

container_name="secrets_$(date +"%Y-%m-%d-%H-%M")"
az storage container create --name "${container_name}"
az storage blob upload-batch --destination "${container_name}" --source "/secrets"
