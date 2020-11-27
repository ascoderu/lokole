#TODO: Ensure all outputs match TF format. setup.sh outputs found below.
/*
output "Namespace Connection String" {
  value = "${azurerm_servicebus_namespace.example.default_primary_connection_string}"
}

output "Shared Access Policy PrimaryKey" {
  value = "${azurerm_servicebus_namespace.example.default_primary_key}"
}
*/

# "appinsightsName": {
#       "type": "string",
#       "value": "[variables('appinsightsName')]"
#     },
# "appinsightsKey": {
#     "type": "string",
#     "value": "[reference(resourceId('Microsoft.Insights/components', variables('appinsightsName')), '2014-04-01').InstrumentationKey]"
# },
# "clientBlobsName": {
#     "type": "string",
#     "value": "[variables('clientBlobsName')]"
# },
# "clientBlobsKey": {
#     "type": "string",
#     "value": "[listKeys(resourceId('Microsoft.Storage/storageAccounts', variables('clientBlobsName')), '2016-01-01').keys[0].value]"
# },
# "serverBlobsName": {
#     "type": "string",
#     "value": "[variables('serverBlobsName')]"
# },
# "serverBlobsKey": {
#     "type": "string",
#     "value": "[listKeys(resourceId('Microsoft.Storage/storageAccounts', variables('serverBlobsName')), '2016-01-01').keys[0].value]"
# },
# "serverTablesName": {
#     "type": "string",
#     "value": "[variables('serverTablesName')]"
# },
# "serverTablesKey": {
#     "type": "string",
#     "value": "[listKeys(resourceId('Microsoft.Storage/storageAccounts', variables('serverTablesName')), '2016-01-01').keys[0].value]"
# },
# "serverQueuesName": {
#     "type": "string",
#     "value": "[variables('serverQueuesName')]"
# },
# "serverQueuesSasName": {
#     "type": "string",
#     "value": "[variables('serverQueuesSasName')]"
# },
# "serverQueuesSasKey": {
#     "type": "string",
#     "value": "[listKeys(resourceId('Microsoft.ServiceBus/namespaces/AuthorizationRules', variables('serverQueuesName'), variables('serverQueuesSasName')), '2017-04-01').primaryKey]"
# }


# The following is output:
# cat >/secrets/azure.env <<EOF
# RESOURCE_GROUP=${RESOURCE_GROUP_NAME}
# LOKOLE_EMAIL_SERVER_APPINSIGHTS_KEY=$(jq -r .properties.outputs.appinsightsKey.value /tmp/deployment.json)
# LOKOLE_CLIENT_AZURE_STORAGE_KEY=$(jq -r .properties.outputs.clientBlobsKey.value /tmp/deployment.json)
# LOKOLE_CLIENT_AZURE_STORAGE_NAME=$(jq -r .properties.outputs.clientBlobsName.value /tmp/deployment.json)
# LOKOLE_CLIENT_AZURE_STORAGE_HOST=
# LOKOLE_CLIENT_AZURE_STORAGE_SECURE=True
# LOKOLE_EMAIL_SERVER_AZURE_BLOBS_KEY=$(jq -r .properties.outputs.serverBlobsKey.value /tmp/deployment.json)
# LOKOLE_EMAIL_SERVER_AZURE_BLOBS_NAME=$(jq -r .properties.outputs.serverBlobsName.value /tmp/deployment.json)
# LOKOLE_EMAIL_SERVER_AZURE_BLOBS_HOST=
# LOKOLE_EMAIL_SERVER_AZURE_BLOBS_SECURE=True
# LOKOLE_EMAIL_SERVER_AZURE_TABLES_KEY=$(jq -r .properties.outputs.serverTablesKey.value /tmp/deployment.json)
# LOKOLE_EMAIL_SERVER_AZURE_TABLES_NAME=$(jq -r .properties.outputs.serverTablesName.value /tmp/deployment.json)
# LOKOLE_EMAIL_SERVER_AZURE_TABLES_HOST=
# LOKOLE_EMAIL_SERVER_AZURE_TABLES_SECURE=True
# LOKOLE_EMAIL_SERVER_QUEUES_NAMESPACE=$(jq -r .properties.outputs.serverQueuesName.value /tmp/deployment.json)
# LOKOLE_EMAIL_SERVER_QUEUES_SAS_NAME=$(jq -r .properties.outputs.serverQueuesSasName.value /tmp/deployment.json)
# LOKOLE_EMAIL_SERVER_QUEUES_SAS_KEY=$(jq -r .properties.outputs.serverQueuesSasKey.value /tmp/deployment.json)
# EOF
