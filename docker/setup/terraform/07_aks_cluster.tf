resource "azurerm_kubernetes_cluster" "default" {
  name                = "${random_pet.prefix.id}-aks"
  location            = var.location
  resource_group_name = var.KUBERNETES_RESOURCE_GROUP_NAME
  dns_prefix          = "${random_pet.prefix.id}-k8s"
  kubernetes_version = "${var.k8s_version}"

  default_node_pool {
    name            = var.k8sname
    node_count      = var.KUBERNETES_NODE_COUNT
    vm_size         = var.KUBERNETES_NODE_SKU
    os_disk_size_gb = var.os_disk_size
  }

  service_principal {
    client_id     = var.SP_APPID
    client_secret = var.SP_PASSWORD
  }

  role_based_access_control {
    enabled = true
  }

  addon_profile {
  }

  tags = {
    environment = "Demo"
  }
}