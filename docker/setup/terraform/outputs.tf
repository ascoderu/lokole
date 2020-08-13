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