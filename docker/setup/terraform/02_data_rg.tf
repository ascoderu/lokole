# ------------------------------
# Data Resource Group
# ------------------------------

# Create a data resource group if it doesn't exist
resource "azurerm_resource_group" "data" {
  name     = "${var.RESOURCE_GROUP_NAME}data"
  location = var.location

  tags = {}
}

# Generate random text for a unique storage account name
resource "random_id" "randomId" {
  keepers = {
    # Generate a new ID only when a new resource group is defined
    resource_group = azurerm_resource_group.vm.name
  }
  
  byte_length = 3
}

# Create server table storage account if it doesn't exist
resource "azurerm_storage_account" "serverTablesName" {
  name                      = "${var.serverTablesName}${random_id.randomId.hex}"
  resource_group_name       = azurerm_resource_group.data.name
  location                  = azurerm_resource_group.data.location
  account_kind              = "Storage"
  account_tier              = "Standard"
  account_replication_type  = "GRS"
  allow_blob_public_access  = true
  enable_https_traffic_only = false

  network_rules {
    default_action = "Allow"
    bypass         = ["AzureServices"]
    ip_rules       = []     
  }

  tags = {}
}

# Create server blob storage account if it doesn't exist
resource "azurerm_storage_account" "serverBlobsName" {
  name                      = "${var.serverBlobsName}${random_id.randomId.hex}"
  resource_group_name       = azurerm_resource_group.data.name
  location                  = azurerm_resource_group.data.location
  account_kind              = "Storage"
  account_tier              = "Standard"
  account_replication_type  = "GRS"
  allow_blob_public_access  = true
  enable_https_traffic_only = false

  network_rules {
    default_action = "Allow"
    bypass         = ["AzureServices"]
    ip_rules       = []     
  }

  tags = {}
}

# Create client blob storage account if it doesn't exist
resource "azurerm_storage_account" "clientBlobsName" {
  name                      = "${var.clientBlobsName}${random_id.randomId.hex}"
  resource_group_name       = azurerm_resource_group.data.name
  location                  = azurerm_resource_group.data.location
  account_kind              = "Storage"
  account_tier              = "Standard"
  account_replication_type  = "GRS"
  allow_blob_public_access  = true
  enable_https_traffic_only = false

  network_rules {
    default_action = "Allow"
    bypass         = ["AzureServices"]
    ip_rules       = []     
  }

  tags = {}
}

resource "azurerm_storage_container" "clientsauth" {
  name                  = "clientsauth"
  storage_account_name  = azurerm_storage_account.serverTablesName.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "pendingemails" {
  name                  = "pendingemails"
  storage_account_name  = azurerm_storage_account.serverTablesName.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "users" {
  name                  = "users"
  storage_account_name  = azurerm_storage_account.serverTablesName.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "emails" {
  name                  = "emails"
  storage_account_name  = azurerm_storage_account.serverBlobsName.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "mailbox" {
  name                  = "mailbox"
  storage_account_name  = azurerm_storage_account.serverBlobsName.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "secretsopwencluster" {
  name                  = "secretsopwencluster"
  storage_account_name  = azurerm_storage_account.serverBlobsName.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "sendgridinboundemails" {
  name                  = "sendgridinboundemails"
  storage_account_name  = azurerm_storage_account.serverBlobsName.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "compressedpackages" {
  name                  = "compressedpackages"
  storage_account_name  = azurerm_storage_account.clientBlobsName.name
  container_access_type = "private"
}

# Create a server queue if it doesn't exist
resource "azurerm_servicebus_namespace" "data" {
  name                = var.serverQueuesName
  location            = azurerm_resource_group.data.location
  resource_group_name = azurerm_resource_group.data.name
  sku                 = "Standard"
  zone_redundant      = false
}

resource "azurerm_servicebus_namespace_authorization_rule" "data" {
  name                = var.serverQueuesSasName
  namespace_name      = azurerm_servicebus_namespace.data.name
  resource_group_name = azurerm_resource_group.data.name
  send                = true
  listen              = true
  manage              = true
}

#! Verify if this one is created automatically
# resource "azurerm_servicebus_namespace_authorization_rule" "data" {
#     name                = "RootManageSharedAccessKey"
#     namespace_name      = "${azurerm_servicebus_namespace.data.name}"
#     resource_group_name = "${azurerm_resource_group.data.name}"
#     send                = true
#     listen              = true
#     manage              = true
# }

#! Verify if this one is created automatically
# resource "azurerm_servicebus_topic" "data" {
#     name                = "${var.RESOURCE_GROUP_NAME}-sbtopic"
#     resource_group_name = "${azurerm_resource_group.data.name}"
#     namespace_name      = "${azurerm_servicebus_namespace.data.name}"
#     enable_partitioning = true
# }

#! Verify if this one is created automatically
# resource "azurerm_servicebus_subscription" "data" {
#     name                = "${var.RESOURCE_GROUP_NAME}-sbsubscription"
#     resource_group_name = "${azurerm_resource_group.data.name}"
#     namespace_name      = "${azurerm_servicebus_namespace.data.name}"
#     topic_name          = "${azurerm_servicebus_topic.data.name}"
#     max_delivery_count  = 1
# }

resource "azurerm_servicebus_queue" "serverQueueSendgridMime" {
  name                = var.serverQueueSendgridMime
  resource_group_name = azurerm_resource_group.data.name
  namespace_name      = azurerm_servicebus_namespace.data.name
  max_size_in_megabytes = 5120

  # Optional Values
  lock_duration                           = "PT1M"
  requires_duplicate_detection            = false
  requires_session                        = false
  default_message_ttl                     = "P14D"
  dead_lettering_on_message_expiration    = false
  duplicate_detection_history_time_window = "PT10M"
  max_delivery_count                      = 10
  status                                  = "Active"
  enable_partitioning                     = false
  enable_express                          = false
}

resource "azurerm_servicebus_queue" "serverQueueEmailSend" {
  name                = var.serverQueueEmailSend
  resource_group_name = azurerm_resource_group.data.name
  namespace_name      = azurerm_servicebus_namespace.data.name
  max_size_in_megabytes = 5120

  # Optional Values
  lock_duration                           = "PT1M"
  requires_duplicate_detection            = false
  requires_session                        = false
  default_message_ttl                     = "P14D"
  dead_lettering_on_message_expiration    = false
  duplicate_detection_history_time_window = "PT10M"
  max_delivery_count                      = 10
  status                                  = "Active"
  enable_partitioning                     = false
  enable_express                          = false
}

resource "azurerm_servicebus_queue" "serverQueueClientPackage" {
  name                = var.serverQueueClientPackage
  resource_group_name = azurerm_resource_group.data.name
  namespace_name      = azurerm_servicebus_namespace.data.name
  max_size_in_megabytes = 5120

  # Optional Values
  lock_duration                           = "PT1M"
  requires_duplicate_detection            = false
  requires_session                        = false
  default_message_ttl                     = "P14D"
  dead_lettering_on_message_expiration    = false
  duplicate_detection_history_time_window = "PT10M"
  max_delivery_count                      = 10
  status                                  = "Active"
  enable_partitioning                     = false
  enable_express                          = false
}

resource "azurerm_servicebus_queue" "mailboxreceived" {
  name                = "mailboxreceived"
  resource_group_name = azurerm_resource_group.data.name
  namespace_name      = azurerm_servicebus_namespace.data.name
  max_size_in_megabytes = 1024

  # Optional Values
  lock_duration                           = "PT1M"
  requires_duplicate_detection            = false
  requires_session                        = false
  default_message_ttl                     = "P14D"
  dead_lettering_on_message_expiration    = false
  duplicate_detection_history_time_window = "PT10M"
  max_delivery_count                      = 10
  status                                  = "Active"
  enable_partitioning                     = false
  enable_express                          = false
}

resource "azurerm_servicebus_queue" "mailboxsent" {
  name                = "mailboxsent"
  resource_group_name = azurerm_resource_group.data.name
  namespace_name      = azurerm_servicebus_namespace.data.name
  max_size_in_megabytes = 1024

  # Optional Values
  lock_duration                           = "PT1M"
  requires_duplicate_detection            = false
  requires_session                        = false
  default_message_ttl                     = "P14D"
  dead_lettering_on_message_expiration    = false
  duplicate_detection_history_time_window = "PT10M"
  max_delivery_count                      = 10
  status                                  = "Active"
  enable_partitioning                     = false
  enable_express                          = false
}

resource "azurerm_servicebus_queue" "register" {
  name                = "register"
  resource_group_name = azurerm_resource_group.data.name
  namespace_name      = azurerm_servicebus_namespace.data.name
  max_size_in_megabytes = 1024

  # Optional Values
  lock_duration                           = "PT1M"
  requires_duplicate_detection            = false
  requires_session                        = false
  default_message_ttl                     = "P14D"
  dead_lettering_on_message_expiration    = false
  duplicate_detection_history_time_window = "PT10M"
  max_delivery_count                      = 10
  status                                  = "Active"
  enable_partitioning                     = false
  enable_express                          = false
}

resource "azurerm_servicebus_queue" "service" {
  name                = "service"
  resource_group_name = azurerm_resource_group.data.name
  namespace_name      = azurerm_servicebus_namespace.data.name
  max_size_in_megabytes = 1024

  # Optional Values
  lock_duration                           = "PT1M"
  requires_duplicate_detection            = false
  requires_session                        = false
  default_message_ttl                     = "P14D"
  dead_lettering_on_message_expiration    = false
  duplicate_detection_history_time_window = "PT10M"
  max_delivery_count                      = 10
  status                                  = "Active"
  enable_partitioning                     = false
  enable_express                          = false
}
