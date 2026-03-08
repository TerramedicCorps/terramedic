variable "name" {
  description = "Name prefix for the peering resources"
  type        = string
}

variable "requester_vpc_id" {
  description = "VPC ID of the requester (the account initiating the peering)"
  type        = string
}

variable "requester_vpc_cidr" {
  description = "CIDR block of the requester VPC"
  type        = string
}

variable "requester_route_table_ids" {
  description = "Route table IDs in the requester VPC that need routes to the accepter VPC"
  type        = list(string)
}

variable "requester_route_count" {
  description = "Number of requester route tables. Set explicitly to avoid count depending on unknown values."
  type        = number
  default     = null
}

variable "accepter_vpc_id" {
  description = "VPC ID of the accepter (the account accepting the peering)"
  type        = string
}

variable "accepter_vpc_cidr" {
  description = "CIDR block of the accepter VPC"
  type        = string
}

variable "accepter_account_id" {
  description = "AWS account ID of the accepter"
  type        = string
}

variable "accepter_region" {
  description = "AWS region of the accepter VPC"
  type        = string
}

variable "accepter_route_table_ids" {
  description = "Route table IDs in the accepter VPC that need routes to the requester VPC"
  type        = list(string)
}

variable "accepter_route_count" {
  description = "Number of accepter route tables. Set explicitly to avoid count depending on unknown values."
  type        = number
  default     = null
}
