#!/usr/bin/env bash
##
## This script sets up all the required Azure resources for the
## lokole project. The script stores the secrets to
## access the created resources in the folder /secrets as dotenv files.
##
## Required environment variables:
##
##   SP_APPID
##   SP_PASSWORD
##   SP_TENANT
##   SUBSCRIPTION_ID
##   LOCATION
##
## Optional environment variables:
##
##   RESOURCE_GROUP_NAME
##   SERVICE_BUS_SKU
##   STORAGE_ACCOUNT_SKU
##
##   KUBERNETES_RESOURCE_GROUP_NAME
##   KUBERNETES_IMAGE_REGISTRY
##   KUBERNETES_DOCKER_TAG
##   KUBERNETES_NODE_SKU
##   KUBERNETES_NODE_COUNT
##   KUBERNETES_VERSION
##   LOKOLE_DNS_NAME
##

scriptdir="$(dirname "$0")"
scriptname="${BASH_SOURCE[0]}"
# shellcheck disable=SC1090
. "${scriptdir}/utils.sh"

if [[ "$1" = "--help" ]]; then
  usage "${scriptname}"
  exit 0
fi

#
# verify inputs
#

required_env "${scriptname}" "SP_APPID"
required_env "${scriptname}" "SP_PASSWORD"
required_env "${scriptname}" "SP_TENANT"
required_env "${scriptname}" "SUBSCRIPTION_ID"
required_env "${scriptname}" "LOCATION"

#
# connect to azure
#

log "Connecting to Azure"
az login --service-principal -u "${SP_APPID}" -p "${SP_PASSWORD}" -t "${SP_TENANT}"
az account set --subscription "${SUBSCRIPTION_ID}"
az configure --defaults location="${LOCATION}"

#
# setup azure resources
#
if [[ "${DEPLOY_SERVICES}" != "no" ]]; then

required_env "${scriptname}" "RESOURCE_GROUP_NAME"

use_resource_group "${RESOURCE_GROUP_NAME}"

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
LOKOLE_CLIENT_AZURE_STORAGE_HOST=
LOKOLE_CLIENT_AZURE_STORAGE_SECURE=True
LOKOLE_EMAIL_SERVER_AZURE_BLOBS_KEY=$(jq -r .properties.outputs.serverBlobsKey.value /tmp/deployment.json)
LOKOLE_EMAIL_SERVER_AZURE_BLOBS_NAME=$(jq -r .properties.outputs.serverBlobsName.value /tmp/deployment.json)
LOKOLE_EMAIL_SERVER_AZURE_BLOBS_HOST=
LOKOLE_EMAIL_SERVER_AZURE_BLOBS_SECURE=True
LOKOLE_EMAIL_SERVER_AZURE_TABLES_KEY=$(jq -r .properties.outputs.serverTablesKey.value /tmp/deployment.json)
LOKOLE_EMAIL_SERVER_AZURE_TABLES_NAME=$(jq -r .properties.outputs.serverTablesName.value /tmp/deployment.json)
LOKOLE_EMAIL_SERVER_AZURE_TABLES_HOST=
LOKOLE_EMAIL_SERVER_AZURE_TABLES_SECURE=True
LOKOLE_EMAIL_SERVER_QUEUES_NAMESPACE=$(jq -r .properties.outputs.serverQueuesName.value /tmp/deployment.json)
LOKOLE_EMAIL_SERVER_QUEUES_SAS_NAME=$(jq -r .properties.outputs.serverQueuesSasName.value /tmp/deployment.json)
LOKOLE_EMAIL_SERVER_QUEUES_SAS_KEY=$(jq -r .properties.outputs.serverQueuesSasKey.value /tmp/deployment.json)
EOF

fi

#
# create production deployment
#
if [[ "${DEPLOY_COMPUTE}" != "no" ]]; then

if [[ -z "${KUBERNETES_RESOURCE_GROUP_NAME}" ]] || [[ -z "${KUBERNETES_NODE_COUNT}" ]] || [[ -z "${KUBERNETES_NODE_SKU}" ]] || [[ -z "${KUBERNETES_VERSION}" ]]; then
  log "Skipping production deployment to kubernetes since KUBERNETES_RESOURCE_GROUP_NAME, KUBERNETES_NODE_COUNT, or KUBERNETES_NODE_SKU, or KUBERNETES_VERSION are not set"
  exit 0
fi

k8sname="opwencluster$(generate_identifier 8)"
helmname="opwenserver$(generate_identifier 8)"

log "Creating kubernetes v${KUBERNETES_VERSION} cluster ${k8sname}"

use_resource_group "${KUBERNETES_RESOURCE_GROUP_NAME}"

az provider register --wait --namespace Microsoft.Network
az provider register --wait --namespace Microsoft.Storage
az provider register --wait --namespace Microsoft.Compute
az provider register --wait --namespace Microsoft.ContainerService

az aks create \
  --kubernetes-version "${KUBERNETES_VERSION}" \
  --service-principal "${SP_APPID}" \
  --client-secret "${SP_PASSWORD}" \
  --name "${k8sname}" \
  --node-count "${KUBERNETES_NODE_COUNT}" \
  --node-vm-size "${KUBERNETES_NODE_SKU}" \
  --generate-ssh-keys

az aks get-credentials --name "${k8sname}"

log "Setting up helm in cluster ${k8sname}"

kubectl apply -f- <<< "
apiVersion: v1
kind: ServiceAccount
metadata:
  name: tiller
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: tiller
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
  - kind: ServiceAccount
    name: tiller
    namespace: kube-system
"
helm_init

log "Setting up cert-manager v${CERT_MANAGER_VERSION} in cluster ${k8sname}"

kubectl apply -f "https://raw.githubusercontent.com/jetstack/cert-manager/v${CERT_MANAGER_VERSION}/deploy/manifests/00-crds.yaml"
kubectl create namespace cert-manager
kubectl label namespace cert-manager certmanager.k8s.io/disable-validation=true
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install --name cert-manager --namespace cert-manager --version "v${CERT_MANAGER_VERSION}" jetstack/cert-manager --wait

log "Setting up nginx-ingress in cluster ${k8sname}"

helm repo add nginx-stable https://helm.nginx.com/stable
helm repo update
helm install --name nginx-ingress --version "${NGINX_INGRESS_VERSION}" nginx-stable/nginx-ingress --set controller.replicaCount=3

log "Setting up kubernetes secrets for ${k8sname}"

kubectl create secret generic "azure" --from-env-file "/secrets/azure.env"
kubectl create secret generic "cloudflare" --from-env-file "/secrets/cloudflare.env"
kubectl create secret generic "users" --from-env-file "/secrets/users.env"
kubectl create secret generic "sendgrid" --from-env-file "/secrets/sendgrid.env"

log "Installing application in ${k8sname}"

k8simageregistry="${KUBERNETES_IMAGE_REGISTRY:-ascoderu}"
k8sdockertag="${KUBERNETES_DOCKER_TAG:-latest}"
lokole_dns_name="${LOKOLE_DNS_NAME:-mailserver.lokole.ca}"

while :; do
  helm install \
    --name "${helmname}" \
    --set domain="${lokole_dns_name}" \
    --set version.imageRegistry="${k8simageregistry}" \
    --set version.dockerTag="${k8sdockertag}" \
    "${scriptdir}/helm/opwen_cloudserver"

  # shellcheck disable=SC2181
  if [[ "$?" -ne 0 ]]; then log "Intermittent error for ${helmname}"; sleep 30s; else break; fi
done

while :; do
  ingressip="$(kubectl get service --selector app.kubernetes.io/instance=nginx-ingress --output jsonpath={..ip})"
  if [[ -z "${ingressip}" ]]; then log "Waiting for ${k8sname} public IP"; sleep 30s; else break; fi
done

cp ~/.kube/config /secrets/kube-config
cp ~/.ssh/id_rsa.pub /secrets/kube-id_rsa.pub
cp ~/.ssh/id_rsa /secrets/kube-id_rsa

log "Setting up DNS for ${ingressip}"

cloudflare_zone="$(get_dotenv '/secrets/cloudflare.env' 'LOKOLE_CLOUDFLARE_ZONE')"
cloudflare_user="$(get_dotenv '/secrets/cloudflare.env' 'LOKOLE_CLOUDFLARE_USER')"
cloudflare_key="$(get_dotenv '/secrets/cloudflare.env' 'LOKOLE_CLOUDFLARE_KEY')"
cloudflare_dns_api="https://api.cloudflare.com/client/v4/zones/${cloudflare_zone}/dns_records"

cloudflare_cname_id="$(curl -sX GET "${cloudflare_dns_api}?type=A&name=${lokole_dns_name}" \
  -H "X-Auth-Email: ${cloudflare_user}" \
  -H "X-Auth-Key: ${cloudflare_key}" \
| jq -r '.result[0].id')"

if [[ -n "${cloudflare_cname_id}" ]] && [[ ${cloudflare_cname_id} != "null" ]]; then
  curl -sX PUT "${cloudflare_dns_api}/${cloudflare_cname_id}" \
    -H "X-Auth-Email: ${cloudflare_user}" \
    -H "X-Auth-Key: ${cloudflare_key}" \
    -H "Content-Type: application/json" \
    -d '{"type":"A","name":"'"${lokole_dns_name}"'","content":"'"${ingressip}"'","ttl":1,"proxied":false}'
else
  curl -sX POST "${cloudflare_dns_api}" \
    -H "X-Auth-Email: ${cloudflare_user}" \
    -H "X-Auth-Key: ${cloudflare_key}" \
    -H "Content-Type: application/json" \
    -d '{"type":"A","name":"'"${lokole_dns_name}"'","content":"'"${ingressip}"'","ttl":1,"proxied":false}'
fi

./renew-cert.sh

cat > /secrets/kubedeployment.env << EOF
RESOURCE_GROUP=${KUBERNETES_RESOURCE_GROUP_NAME}
HELM_NAME=${helmname}
APP_IP=${ingressip}
APP_DNS=${lokole_dns_name}
EOF
fi

#
# backup secrets
#

storage_account="$(get_dotenv '/secrets/azure.env' 'LOKOLE_EMAIL_SERVER_AZURE_BLOBS_NAME')"
storage_key="$(get_dotenv '/secrets/azure.env' 'LOKOLE_EMAIL_SERVER_AZURE_BLOBS_KEY')"
container_name="secrets-${k8sname}"

log "Backing up secrets to ${storage_account}/${container_name}"

az storage container create --name "${container_name}" \
  --account-name="${storage_account}" --account-key="${storage_key}"
az storage blob upload-batch --destination "${container_name}" --source "/secrets" \
  --account-name="${storage_account}" --account-key="${storage_key}"
