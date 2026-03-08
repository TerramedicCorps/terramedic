variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
  default     = "terramedic"
}

variable "public_subnet_id" {
  description = "Public subnet ID for the bastion host"
  type        = string
}

variable "bastion_security_group_id" {
  description = "ID of the bastion security group"
  type        = string
}

variable "bastion_key_name" {
  description = "SSH key pair name for the bastion host"
  type        = string
  default     = "terramedic-bastion"
}

variable "bastion_public_key" {
  description = "SSH public key for the bastion host (leave empty to skip key pair creation)"
  type        = string
  default     = ""
  sensitive   = true

  validation {
    condition     = var.bastion_public_key == "" || length(var.bastion_public_key) <= 2048
    error_message = "The bastion_public_key exceeds AWS's limit of 2048 characters."
  }
}

variable "create_new_key_pair" {
  description = "Whether to create a new key pair or use an existing one. Set to false if the key pair already exists in AWS."
  type        = bool
  default     = false
}
