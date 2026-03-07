#!/bin/bash
# Bootstrap a single AWS account for Terraform remote state and GitHub OIDC.
# Creates: S3 state bucket, DynamoDB lock table, GitHub OIDC CloudFormation stack,
# and (for shared account only) a VPC peering accepter role.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions (write to stderr so progress is visible when stdout is piped)
log_info() {
  echo -e "${BLUE}[INFO]${NC} $1" >&2
}

log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1" >&2
}

log_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1" >&2
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Script directory (for finding CloudFormation templates)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Defaults
DEFAULT_REGION="us-east-1"

usage() {
  cat <<EOF
Bootstrap a single AWS account for Terraform remote state and GitHub OIDC.

Usage: $0 [OPTIONS]

OPTIONS:
    -e, --environment ENV    Environment name: shared, prod, or dev (required)
    --github-org ORG         GitHub org or user name (required)
    --github-repo REPO       GitHub repository name (required)
    --prod-account-id ID     Prod AWS account ID (required for shared environment)
    --dev-account-id ID      Dev AWS account ID (required for shared environment)
    -p, --profile PROFILE    AWS CLI profile to use (optional)
    -r, --region REGION      AWS region (default: $DEFAULT_REGION)
    -h, --help               Show this help message

EXAMPLES:
    $0 --environment shared --github-org TerramedicCorps --github-repo terramedic --profile terramedic-shared --prod-account-id 214888068332 --dev-account-id 682120331907
    $0 --environment prod --github-org TerramedicCorps --github-repo terramedic --profile terramedic-prod
    $0 --environment dev --github-org TerramedicCorps --github-repo terramedic

EOF
}

# Parse arguments
ENVIRONMENT=""
GITHUB_ORG=""
GITHUB_REPO=""
PROD_ACCOUNT_ID=""
DEV_ACCOUNT_ID=""
AWS_PROFILE_ARG=""
REGION="$DEFAULT_REGION"

while [[ $# -gt 0 ]]; do
  case $1 in
    -e | --environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --github-org)
      GITHUB_ORG="$2"
      shift 2
      ;;
    --github-repo)
      GITHUB_REPO="$2"
      shift 2
      ;;
    --prod-account-id)
      PROD_ACCOUNT_ID="$2"
      shift 2
      ;;
    --dev-account-id)
      DEV_ACCOUNT_ID="$2"
      shift 2
      ;;
    -p | --profile)
      AWS_PROFILE_ARG="--profile $2"
      shift 2
      ;;
    -r | --region)
      REGION="$2"
      shift 2
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      log_error "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

# Validate required arguments
if [[ -z "$ENVIRONMENT" ]]; then
  log_error "Environment is required"
  usage
  exit 1
fi

if [[ -z "$GITHUB_ORG" || -z "$GITHUB_REPO" ]]; then
  log_error "--github-org and --github-repo are required"
  usage
  exit 1
fi

if [[ "$ENVIRONMENT" != "shared" && "$ENVIRONMENT" != "prod" && "$ENVIRONMENT" != "dev" ]]; then
  log_error "Environment must be one of: shared, prod, dev"
  exit 1
fi

if [[ "$ENVIRONMENT" == "shared" && ( -z "$PROD_ACCOUNT_ID" || -z "$DEV_ACCOUNT_ID" ) ]]; then
  log_error "--prod-account-id and --dev-account-id are required for the shared environment"
  usage
  exit 1
fi

# Helper to run AWS CLI with optional profile
aws_cmd() {
  # shellcheck disable=SC2086
  aws $AWS_PROFILE_ARG --region "$REGION" "$@"
}

# Look up account ID
log_info "Looking up AWS account ID..."
ACCOUNT_ID=$(aws_cmd sts get-caller-identity --query Account --output text)
log_success "Account ID: $ACCOUNT_ID"

# Configuration
S3_BUCKET_NAME="terramedic-terraform-state-${ACCOUNT_ID}"
DYNAMODB_TABLE_NAME="terramedic-terraform-locks"

# --- Step 1: S3 state bucket ---
log_info "Checking S3 state bucket: $S3_BUCKET_NAME"

if ! aws_cmd s3api head-bucket --bucket "$S3_BUCKET_NAME" 2>/dev/null; then
  log_info "Creating S3 bucket for Terraform state..."
  CREATE_BUCKET_ARGS=(s3api create-bucket --bucket "$S3_BUCKET_NAME" --region "$REGION")
  if [[ "$REGION" != "us-east-1" ]]; then
    CREATE_BUCKET_ARGS+=(--create-bucket-configuration "LocationConstraint=${REGION}")
  fi
  aws_cmd "${CREATE_BUCKET_ARGS[@]}"

  # Enable versioning
  aws_cmd s3api put-bucket-versioning \
    --bucket "$S3_BUCKET_NAME" \
    --versioning-configuration Status=Enabled

  # Enable encryption
  aws_cmd s3api put-bucket-encryption \
    --bucket "$S3_BUCKET_NAME" \
    --server-side-encryption-configuration '{
      "Rules": [
        {
          "ApplyServerSideEncryptionByDefault": {
            "SSEAlgorithm": "AES256"
          }
        }
      ]
    }'

  # Block public access
  aws_cmd s3api put-public-access-block \
    --bucket "$S3_BUCKET_NAME" \
    --public-access-block-configuration '{
      "BlockPublicAcls": true,
      "IgnorePublicAcls": true,
      "BlockPublicPolicy": true,
      "RestrictPublicBuckets": true
    }'

  # Lifecycle policies
  aws_cmd s3api put-bucket-lifecycle-configuration \
    --bucket "$S3_BUCKET_NAME" \
    --lifecycle-configuration '{
      "Rules": [
        {
          "ID": "DeleteTestStates",
          "Status": "Enabled",
          "Filter": {"Prefix": "tests/"},
          "Expiration": {"Days": 7}
        },
        {
          "ID": "DeleteOldVersions",
          "Status": "Enabled",
          "Filter": {},
          "NoncurrentVersionExpiration": {"NoncurrentDays": 90}
        }
      ]
    }'

  log_success "S3 bucket created and configured: $S3_BUCKET_NAME"
else
  log_warning "S3 bucket already exists: $S3_BUCKET_NAME"
fi

# --- Step 2: DynamoDB lock table ---
log_info "Checking DynamoDB lock table: $DYNAMODB_TABLE_NAME"

if ! aws_cmd dynamodb describe-table --table-name "$DYNAMODB_TABLE_NAME" >/dev/null 2>&1; then
  log_info "Creating DynamoDB table for Terraform state locking..."
  aws_cmd dynamodb create-table \
    --table-name "$DYNAMODB_TABLE_NAME" \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

  log_success "DynamoDB table created: $DYNAMODB_TABLE_NAME"
else
  log_warning "DynamoDB table already exists: $DYNAMODB_TABLE_NAME"
fi

# --- Step 3: GitHub OIDC CloudFormation stack ---
OIDC_STACK_NAME="terramedic-github-oidc-${ENVIRONMENT}"
log_info "Deploying CloudFormation stack: $OIDC_STACK_NAME"

aws_cmd cloudformation deploy \
  --template-file "${SCRIPT_DIR}/github-oidc-role.cfn.yml" \
  --stack-name "$OIDC_STACK_NAME" \
  --parameter-overrides \
    "Environment=${ENVIRONMENT}" \
    "GitHubOrg=${GITHUB_ORG}" \
    "GitHubRepo=${GITHUB_REPO}" \
  --capabilities CAPABILITY_NAMED_IAM \
  --no-fail-on-empty-changeset

OIDC_ROLE_ARN=$(aws_cmd cloudformation describe-stacks \
  --stack-name "$OIDC_STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='RoleArn'].OutputValue" \
  --output text)

log_success "GitHub OIDC role deployed: $OIDC_ROLE_ARN"

# --- Step 4: Cross-account state bucket policy (shared account only) ---
# Prod and dev accounts read the shared Terraform state via terraform_remote_state.
# S3 cross-account access requires both an IAM policy on the requester AND a
# bucket policy on the source bucket.
if [[ "$ENVIRONMENT" == "shared" ]]; then
  log_info "Adding cross-account read policy to state bucket for prod/dev OIDC roles..."
  aws_cmd s3api put-bucket-policy \
    --bucket "$S3_BUCKET_NAME" \
    --policy "{
      \"Version\": \"2012-10-17\",
      \"Statement\": [
        {
          \"Sid\": \"AllowCrossAccountTerraformStateRead\",
          \"Effect\": \"Allow\",
          \"Principal\": {
            \"AWS\": [
              \"arn:aws:iam::${PROD_ACCOUNT_ID}:role/github-actions-prod\",
              \"arn:aws:iam::${DEV_ACCOUNT_ID}:role/github-actions-dev\"
            ]
          },
          \"Action\": [
            \"s3:GetObject\",
            \"s3:ListBucket\"
          ],
          \"Resource\": [
            \"arn:aws:s3:::${S3_BUCKET_NAME}\",
            \"arn:aws:s3:::${S3_BUCKET_NAME}/*\"
          ]
        }
      ]
    }"
  log_success "Cross-account bucket policy applied"
fi

# --- Step 5: VPC peering accepter role (shared account only) ---
if [[ "$ENVIRONMENT" == "shared" ]]; then
  PEERING_STACK_NAME="terramedic-vpc-peering-accepter"
  log_info "Deploying CloudFormation stack: $PEERING_STACK_NAME (shared account only)"

  aws_cmd cloudformation deploy \
    --template-file "${SCRIPT_DIR}/peering-role.cfn.yml" \
    --stack-name "$PEERING_STACK_NAME" \
    --parameter-overrides \
      "ProdAccountId=${PROD_ACCOUNT_ID}" \
      "DevAccountId=${DEV_ACCOUNT_ID}" \
    --capabilities CAPABILITY_NAMED_IAM \
    --no-fail-on-empty-changeset

  PEERING_ROLE_ARN=$(aws_cmd cloudformation describe-stacks \
    --stack-name "$PEERING_STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='RoleArn'].OutputValue" \
    --output text)

  log_success "VPC peering accepter role deployed: $PEERING_ROLE_ARN"
fi

# --- Summary (to stderr so it's visible when stdout is piped) ---
echo >&2
log_success "Bootstrap complete for $ENVIRONMENT account ($ACCOUNT_ID)"
echo -e "  S3 bucket:      ${GREEN}${S3_BUCKET_NAME}${NC}" >&2
echo -e "  DynamoDB table:  ${GREEN}${DYNAMODB_TABLE_NAME}${NC}" >&2
echo -e "  OIDC role ARN:   ${GREEN}${OIDC_ROLE_ARN}${NC}" >&2
if [[ "$ENVIRONMENT" == "shared" ]]; then
  echo -e "  Peering role:    ${GREEN}${PEERING_ROLE_ARN}${NC}" >&2
fi

# Output the OIDC role ARN for use by the orchestrator (prefixed for robust parsing)
echo "OIDC_ROLE_ARN=$OIDC_ROLE_ARN"
