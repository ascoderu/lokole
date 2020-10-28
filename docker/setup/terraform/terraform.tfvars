#TODO Using this as an example of the possibility. Given we populate from a docker-compose command,
# I don't know if this will be super useful for us, vice utilising the Default values found in variables.tf
# See: https://learn.hashicorp.com/tutorials/terraform/azure-variables 
SP_APPID                 = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
SP_PASSWORD              = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
SP_TENANT                = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
SUBSCRIPTION_ID          = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
RESOURCE_GROUP_NAME      = "opwen"
vmName                   = "opwenvm"
appinsightsName          = "opwenlogs"
clientBlobsName          = "opwenclient"
serverBlobsName          = "opwenserverblobs"
serverTablesName         = "opwenservertables"
serverQueuesName         = "opwenserverqueues"
serverQueuesSasName      = "celery"
serverQueueSendgridMime  = "inbound"
serverQueueClientPackage = "written"
serverQueueEmailSend     = "send"
location                 = "eastus"