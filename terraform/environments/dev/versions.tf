terraform {
  required_version = ">= 1.12.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.99.0"
    }
    awscc = {
      source  = "hashicorp/awscc"
      version = "~> 1.48.0"
    }
  }
}
