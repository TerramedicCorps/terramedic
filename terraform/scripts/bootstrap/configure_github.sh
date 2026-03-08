#!/bin/bash
# Configure GitHub repository environments and secrets for OIDC-based CI/CD.
# Requires: gh CLI authenticated with repo admin access.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

usage() {
  cat <<EOF
Configure GitHub repository environments and secrets for Terramedic CI/CD.

Usage: $0 [OPTIONS]

OPTIONS:
    --repo ORG/REPO              GitHub repository (required)
    --shared-account-id ID       Shared AWS account ID (required)
    --prod-account-id ID         Prod AWS account ID (required)
    --dev-account-id ID          Dev AWS account ID (required)
    --region REGION              AWS region (default: us-east-1)
    -h, --help                   Show this help message

EOF
}

REPO=""
SHARED_ACCOUNT_ID=""
PROD_ACCOUNT_ID=""
DEV_ACCOUNT_ID=""
REGION="us-east-1"

while [[ $# -gt 0 ]]; do
  case $1 in
    --repo) REPO="$2"; shift 2 ;;
    --shared-account-id) SHARED_ACCOUNT_ID="$2"; shift 2 ;;
    --prod-account-id) PROD_ACCOUNT_ID="$2"; shift 2 ;;
    --dev-account-id) DEV_ACCOUNT_ID="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    -h | --help) usage; exit 0 ;;
    *) log_error "Unknown option: $1"; usage; exit 1 ;;
  esac
done

if [[ -z "$REPO" || -z "$SHARED_ACCOUNT_ID" || -z "$PROD_ACCOUNT_ID" || -z "$DEV_ACCOUNT_ID" ]]; then
  log_error "All options are required"
  usage
  exit 1
fi

# Check gh CLI is available and authenticated
if ! command -v gh &>/dev/null; then
  log_error "gh CLI is not installed. Install it from https://cli.github.com/"
  exit 1
fi

if ! gh auth status &>/dev/null; then
  log_error "gh CLI is not authenticated. Run 'gh auth login' first."
  exit 1
fi

# Create GitHub environments
for env in shared prod dev; do
  log_info "Creating GitHub environment: $env"
  # gh api will create the environment if it doesn't exist
  gh api --method PUT "repos/${REPO}/environments/${env}" --silent 2>/dev/null || true
  log_success "Environment '$env' created/verified"
done

# Set environment-level secrets (OIDC role ARNs)
set_env_secret() {
  local env="$1"
  local name="$2"
  local value="$3"
  log_info "Setting secret $name in environment $env"
  echo "$value" | gh secret set "$name" --repo "$REPO" --env "$env"
}

# AWS_ROLE_ARN for each environment (used by GitHub Actions OIDC)
set_env_secret "shared" "AWS_ROLE_ARN" "arn:aws:iam::${SHARED_ACCOUNT_ID}:role/github-actions-shared"
set_env_secret "prod" "AWS_ROLE_ARN" "arn:aws:iam::${PROD_ACCOUNT_ID}:role/github-actions-prod"
set_env_secret "dev" "AWS_ROLE_ARN" "arn:aws:iam::${DEV_ACCOUNT_ID}:role/github-actions-dev"

# AWS_REGION as an environment variable (not secret)
for env in shared prod dev; do
  log_info "Setting AWS_REGION variable in environment $env"
  gh variable set "AWS_REGION" --repo "$REPO" --env "$env" --body "$REGION"
done

# Shared account ID needed by prod/dev for remote state and VPC peering
set_env_secret "prod" "SHARED_ACCOUNT_ID" "$SHARED_ACCOUNT_ID"
set_env_secret "dev" "SHARED_ACCOUNT_ID" "$SHARED_ACCOUNT_ID"

log_success "GitHub environments and secrets configured successfully"
echo
echo -e "${BLUE}Environments created:${NC} shared, prod, dev"
echo -e "${BLUE}Secrets set:${NC} AWS_ROLE_ARN (per env), SHARED_ACCOUNT_ID (prod/dev)"
echo -e "${BLUE}Variables set:${NC} AWS_REGION (per env)"
