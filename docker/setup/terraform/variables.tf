variable "RESOURCE_GROUP_NAME" {
  type        = string
  default     = "opwenTest"
  description = "The prefix which should be used for all resources in this application."
}

# variable "SUBSCRIPTION_ID" {
#   type        = string
#   description = "Lorum ipsum doler."
# }

# variable "client_id" {
#   type        = string
#   description = "Lorum ipsum doler."
# }

# variable "SP_PASSWORD" {
#   type        = string
#   description = "Lorum ipsum doler."
# }

# variable "SP_TENANT" {
#   type        = string
#   description = "Lorum ipsum doler."
# }

variable "location" {
  type        = string
  default     = "eastus"
  description = "The Azure Region in which all resources in this example should be created."
}

variable "vmName" {
  type        = string
  default     = "opwenvm"
}

variable "appinsightsName" {
  type        = string
  default     = "opwenlogs"
}

variable "clientBlobsName" {
  type        = string
  default     = "opwenclient"
}

variable "serverBlobsName" {
  type        = string
  default     = "opwenserverblobs"
}

variable "serverTablesName" {
  type        = string
  default     = "opwenservertables"
}

variable "serverQueuesName" {
  type        = string
  default     = "opwenserverqueues"
}

variable "serverQueuesSasName" {
  type    = string
  default = "celery"
}

variable "serverQueueSendgridMime" {
  type    = string
  default = "inbound"
}

variable "serverQueueClientPackage" {
  type    = string
  default = "written"
}

variable "serverQueueEmailSend" {
  type    = string
  default = "send"
}