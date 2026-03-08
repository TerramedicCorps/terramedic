# VPC Peering Module
# Creates a VPC peering connection between two accounts (requester and accepter).
# The requester side creates the peering request; the accepter side accepts it.
# Routes are added to both sides for cross-VPC communication.

terraform {
  required_version = ">= 1.12.0"

  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = "~> 5.99.0"
      configuration_aliases = [aws.accepter]
    }
  }
}

# VPC Peering Connection (created by the requester)
resource "aws_vpc_peering_connection" "this" {
  vpc_id        = var.requester_vpc_id
  peer_vpc_id   = var.accepter_vpc_id
  peer_owner_id = var.accepter_account_id
  peer_region   = var.accepter_region
  auto_accept   = false

  tags = {
    Name = "${var.name}-peering"
    Side = "Requester"
  }
}

# Accept the peering connection in the accepter account
resource "aws_vpc_peering_connection_accepter" "this" {
  provider = aws.accepter

  vpc_peering_connection_id = aws_vpc_peering_connection.this.id
  auto_accept               = true

  tags = {
    Name = "${var.name}-peering"
    Side = "Accepter"
  }
}

# Route from requester VPC to accepter VPC
resource "aws_route" "requester_to_accepter" {
  count = coalesce(var.requester_route_count, length(var.requester_route_table_ids))

  route_table_id            = var.requester_route_table_ids[count.index]
  destination_cidr_block    = var.accepter_vpc_cidr
  vpc_peering_connection_id = aws_vpc_peering_connection.this.id

  depends_on = [aws_vpc_peering_connection_accepter.this]
}

# Route from accepter VPC to requester VPC
resource "aws_route" "accepter_to_requester" {
  provider = aws.accepter
  count    = coalesce(var.accepter_route_count, length(var.accepter_route_table_ids))

  route_table_id            = var.accepter_route_table_ids[count.index]
  destination_cidr_block    = var.requester_vpc_cidr
  vpc_peering_connection_id = aws_vpc_peering_connection.this.id

  depends_on = [aws_vpc_peering_connection_accepter.this]
}
