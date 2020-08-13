#TODO:
# [X] - Configure VM
# [] - Configure Opwen Data
# [] - Configure Opwen Server
# [] - Configure Opwen Test
# [] - Configure dashboards
# [] - Verify depends_on aren't necessary. See celery in arm.tempalte.json.
# [] - Delete tags = {} if not necessary


# Configure the Microsoft Azure Provider
provider "azurerm" {
    # The "feature" block is required for AzureRM provider 2.x. 
    # If you're using version 1.x, the "features" block is not allowed.
    version = "~>2.0"

    features {}
}

# ------------------------------
# Server Resource Group
# ------------------------------

# Create the server resource group if it doesn't exist
resource "azurerm_resource_group" "server" {
    name     = "${var.RESOURCE_GROUP_NAME}server"
    location = var.location

    tags = {}
}

# ------------------------------
# Data Resource Group
# ------------------------------

# Create a data resource group if it doesn't exist
resource "azurerm_resource_group" "data" {
    name     = "${var.RESOURCE_GROUP_NAME}data"
    location = var.location

    tags = {}
}

#TODO: data-template.json indicates encryption, cannot find on terraform.
# Create server table storage account if it doesn't exist
resource "azurerm_storage_account" "serverTablesName" {
  name                      = var.serverTablesName
  resource_group_name       = azurerm_resource_group.data.name
  location                  = azurerm_resource_group.data.location
  account_kind              = "Storage"
  account_tier              = "Standard"
  account_replication_type  = "GRS"
  allow_blob_public_access  = true
  enable_https_traffic_only = false

  network_rules {
      default_action = "Allow"
      bypass          = ["AzureServices"]
      ip_rules        = []     
  }

  tags = {}
}

# Create server blob storage account if it doesn't exist
resource "azurerm_storage_account" "serverBlobsName" {
  name                      = var.serverBlobsName
  resource_group_name       = azurerm_resource_group.data.name
  location                  = azurerm_resource_group.data.location
  account_kind              = "Storage"
  account_tier              = "Standard"
  account_replication_type  = "GRS"
  allow_blob_public_access  = true
  enable_https_traffic_only = false

  network_rules {
      default_action = "Allow"
      bypass          = ["AzureServices"]
      ip_rules        = []     
  }

  tags = {}
}

# Create client blob storage account if it doesn't exist
resource "azurerm_storage_account" "clientBlobsName" {
  name                      = var.clientBlobsName
  resource_group_name       = azurerm_resource_group.data.name
  location                  = azurerm_resource_group.data.location
  account_kind              = "Storage"
  account_tier              = "Standard"
  account_replication_type  = "GRS"
  allow_blob_public_access  = true
  enable_https_traffic_only = false

  network_rules {
      default_action = "Allow"
      bypass          = ["AzureServices"]
      ip_rules        = []     
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
    requires_duplicate_detection          = false
    requires_session                        = false
    default_message_ttl                     = "P14D"
    dead_lettering_on_message_expiration    = false
    duplicate_detection_history_time_window = "PT10M"
    max_delivery_count                      = 10
    status                           = "Active"
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
    requires_duplicate_detection          = false
    requires_session                        = false
    default_message_ttl                     = "P14D"
    dead_lettering_on_message_expiration    = false
    duplicate_detection_history_time_window = "PT10M"
    max_delivery_count                      = 10
    status                           = "Active"
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
    requires_duplicate_detection          = false
    requires_session                        = false
    default_message_ttl                     = "P14D"
    dead_lettering_on_message_expiration    = false
    duplicate_detection_history_time_window = "PT10M"
    max_delivery_count                      = 10
    status                           = "Active"
    enable_partitioning                     = false
    enable_express                          = false
}

#! Verify these Queue items aren't populated automatically. It seems they are.
#! https://docs.microsoft.com/en-us/azure/service-bus-messaging/service-bus-queues-topics-subscriptions
resource "azurerm_servicebus_queue" "mailboxreceived" {
    name                = "mailboxreceived"
    resource_group_name = azurerm_resource_group.data.name
    namespace_name      = azurerm_servicebus_namespace.data.name
    max_size_in_megabytes = 1024

    # Optional Values
    lock_duration                           = "PT1M"
    requires_duplicate_detection          = false
    requires_session                        = false
    default_message_ttl                     = "P14D"
    dead_lettering_on_message_expiration    = false
    duplicate_detection_history_time_window = "PT10M"
    max_delivery_count                      = 10
    status                           = "Active"
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
    requires_duplicate_detection          = false
    requires_session                        = false
    default_message_ttl                     = "P14D"
    dead_lettering_on_message_expiration    = false
    duplicate_detection_history_time_window = "PT10M"
    max_delivery_count                      = 10
    status                           = "Active"
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
    requires_duplicate_detection          = false
    requires_session                        = false
    default_message_ttl                     = "P14D"
    dead_lettering_on_message_expiration    = false
    duplicate_detection_history_time_window = "PT10M"
    max_delivery_count                      = 10
    status                           = "Active"
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
    requires_duplicate_detection          = false
    requires_session                        = false
    default_message_ttl                     = "P14D"
    dead_lettering_on_message_expiration    = false
    duplicate_detection_history_time_window = "PT10M"
    max_delivery_count                      = 10
    status                           = "Active"
    enable_partitioning                     = false
    enable_express                          = false
}

# ------------------------------
# Test Resource Group
# ------------------------------

# Create a resource group if it doesn't exist
resource "azurerm_resource_group" "test" {
    name     = "${var.RESOURCE_GROUP_NAME}test"
    location = var.location

    tags = {}
}

# ------------------------------
# Virtual Machine Resource Group
# ------------------------------

# Create a resource group if it doesn't exist
resource "azurerm_resource_group" "vm" {
    name     = var.vmName
    location = var.location

    tags = {}
}

#! Current infra uses port 24 on vnet, azure docs indicate to use 16 and 24 on subnet
# https://docs.microsoft.com/en-us/azure/developer/terraform/create-linux-virtual-machine-with-infrastructure
# Create virtual network
resource "azurerm_virtual_network" "vm" {
    name                 = "vm-vnet"
    location             = var.location
    resource_group_name  = azurerm_resource_group.vm.name
    address_space        = ["10.0.0.0/16"]

    # subnet {
    #     name           = "subnet1"
    #     address_prefix = "10.0.1.0/24"
    # }

    tags = {}
}

#! Verify address prefix. Current infra has "10.0.0.0/24" which is the same as primary
resource "azurerm_subnet" "vmsubnet" {
  name                 = "vmsubnet"
  resource_group_name  = azurerm_resource_group.vm.name
  virtual_network_name = azurerm_virtual_network.vm.name
  address_prefix       = "10.0.2.0/24"
}

# Create public IPs
resource "azurerm_public_ip" "vm" {
    name                         = "vm-ip"
    location                     = var.location
    resource_group_name          = azurerm_resource_group.vm.name
    allocation_method            = "Dynamic"
    sku                          = "Basic"
    ip_version                   = "IPv4"
    domain_name_label            = "opwenvmtest"
    #! Verify if this is necessary
    #reverse_fqdn                 = "opwenvmtest.${var.location}.cloudapp.azure.com"
    idle_timeout_in_minutes      = 4

    tags = {}
}

# Create Network Security Group and rule
resource "azurerm_network_security_group" "vm" {
    name                = "vm-nsg"
    location            = var.location
    resource_group_name = azurerm_resource_group.vm.name
    
    security_rule {
        name                       = "SSH"
        priority                   = 300
        direction                  = "Inbound"
        access                     = "Allow"
        protocol                   = "Tcp"
        source_port_range          = "*"
        destination_port_range     = "22"
        source_address_prefix      = "*"
        destination_address_prefix = "*"
    }
    security_rule {
        name                       = "HTTPS"
        priority                   = 320
        direction                  = "Inbound"
        access                     = "Allow"
        protocol                   = "Tcp"
        source_port_range          = "*"
        destination_port_range     = "443"
        source_address_prefix      = "*"
        destination_address_prefix = "*"
    }
    security_rule {
        name                       = "HTTP"
        priority                   = 340
        direction                  = "Inbound"
        access                     = "Allow"
        protocol                   = "Tcp"
        source_port_range          = "*"
        destination_port_range     = "80"
        source_address_prefix      = "*"
        destination_address_prefix = "*"
    }
    # TODO: Add other security rules
    # Inbound: HTTPS / HTTP / AllowVnetInbound / AllowAzureLoadBalancerInBound / DenyAllInBound
    # Outbound: AllowVnetOutBound / AllowInternetOutBound / DenyAllOutBound

    tags = {}
}

# Create network interface
# https://www.terraform.io/docs/providers/azurerm/r/network_interface.html
resource "azurerm_network_interface" "vm" {
    name                      = "vm-nic"
    location                  = var.location
    resource_group_name       = azurerm_resource_group.vm.name

    ip_configuration {
        name                          = "vm-nicConfiguration"
        private_ip_address_allocation = "Dynamic"
        public_ip_address_id          = azurerm_public_ip.vm.id
        subnet_id                     = azurerm_subnet.vmsubnet.id
        primary                       = true
    }

    tags = {}
}

# Connect the security group to the network interface
resource "azurerm_network_interface_security_group_association" "vm" {
    network_interface_id      = azurerm_network_interface.vm.id
    network_security_group_id = azurerm_network_security_group.vm.id
}

# Generate random text for a unique storage account name
resource "random_id" "randomId" {
    keepers = {
        # Generate a new ID only when a new resource group is defined
        resource_group = azurerm_resource_group.vm.name
    }
    
    byte_length = 8
}

#! Verify whether this is necessary
# Create storage account for boot diagnostics
resource "azurerm_storage_account" "vm" {
    name                        = "diag${random_id.randomId.hex}"
    resource_group_name         = azurerm_resource_group.vm.name
    location                    = var.location
    account_tier                = "Standard"
    account_replication_type    = "LRS"

    tags = {}
}

# Create (and display) an SSH key
resource "tls_private_key" "vm" {
  algorithm = "RSA"
  rsa_bits = 4096
}
output "tls_private_key" { value = tls_private_key.vm.private_key_pem }

# Create virtual machine
resource "azurerm_linux_virtual_machine" "vm" {
    name                  = "vm"
    location              = var.location
    resource_group_name   = azurerm_resource_group.vm.name
    network_interface_ids = [azurerm_network_interface.vm.id]
    size                  = "Standard_D4s_v3"
    provision_vm_agent    = true

    os_disk {
        name                 = "vm-disk"
        caching              = "ReadWrite"
        storage_account_type = "Premium_LRS"
        # disk_size must exceed that of the image of the vm if declared explicitly.
        # disk_size_gb         = 30
    }

    source_image_reference {
        publisher = "Canonical"
        offer     = "UbuntuServer"
        sku       = "18.04-LTS"
        version   = "latest"
    }

    admin_username                  = var.RESOURCE_GROUP_NAME
    disable_password_authentication = true
    allow_extension_operations      = true
        
    admin_ssh_key {
        username       = var.RESOURCE_GROUP_NAME
        public_key     = tls_private_key.vm.public_key_openssh
    }

    boot_diagnostics {
        storage_account_uri = azurerm_storage_account.vm.primary_blob_endpoint
    }

    tags = {}
}