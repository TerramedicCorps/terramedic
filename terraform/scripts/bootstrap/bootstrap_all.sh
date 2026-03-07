#!/bin/bash
# Orchestrator: bootstrap all AWS accounts and configure GitHub environments.
# Runs bootstrap_account.sh for each account, then configure_github.sh.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Defaults
DEFAULT_REGION="us-east-1"

usage() {
  cat <<EOF
Bootstrap all AWS accounts and configure GitHub environments.

Usage: $0 [OPTIONS]

OPTIONS:
    --shared-profile PROFILE  aws-vault profile for shared account (default: terramedic-shared)
    --prod-profile PROFILE    aws-vault profile for prod account (default: terramedic-prod)
    --dev-profile PROFILE     aws-vault profile for dev account (default: terramedic-dev)
    --github-org ORG          GitHub org or user name (default: TerramedicCorps)
    --github-repo REPO        GitHub repository name (default: terramedic)
    --region REGION           AWS region (default: $DEFAULT_REGION)
    --skip-github             Skip GitHub environment configuration
    -h, --help                Show this help message

EXAMPLES:
    $0
    $0 --shared-profile terramedic-shared --prod-profile terramedic-prod --dev-profile terramedic-dev
    $0 --skip-github

EOF
}

# Parse arguments
SHARED_PROFILE="terramedic-shared"
PROD_PROFILE="terramedic-prod"
DEV_PROFILE="terramedic-dev"
GITHUB_ORG="TerramedicCorps"
GITHUB_REPO="terramedic"
REGION="$DEFAULT_REGION"
SKIP_GITHUB=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --shared-profile)
      SHARED_PROFILE="$2"
      shift 2
      ;;
    --prod-profile)
      PROD_PROFILE="$2"
      shift 2
      ;;
    --dev-profile)
      DEV_PROFILE="$2"
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
    --region)
      REGION="$2"
      shift 2
      ;;
    --skip-github)
      SKIP_GITHUB=true
      shift
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

# Helper to extract the OIDC role ARN from bootstrap output.
# bootstrap_account.sh prints "OIDC_ROLE_ARN=<arn>" as its final line.
extract_role_arn() {
  grep '^OIDC_ROLE_ARN=' | tail -n 1 | cut -d= -f2-
}

# Helper to extract the account ID from an ARN (arn:aws:iam::ACCOUNT_ID:role/...)
extract_account_id_from_arn() {
  local arn="$1"
  echo "$arn" | cut -d: -f5
}

echo
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Bootstrap All AWS Accounts${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# --- Step 1: Bootstrap prod account ---
log_info "Step 1/4: Bootstrapping prod account..."
PROD_ROLE_ARN=$(aws-vault exec "$PROD_PROFILE" -- "${SCRIPT_DIR}/bootstrap_account.sh" \
  --environment prod \
  --github-org "$GITHUB_ORG" \
  --github-repo "$GITHUB_REPO" \
  --region "$REGION" | extract_role_arn)
PROD_ACCOUNT_ID=$(extract_account_id_from_arn "$PROD_ROLE_ARN")
log_success "Prod account bootstrapped (role: $PROD_ROLE_ARN)"
echo

# --- Step 2: Bootstrap dev account ---
log_info "Step 2/4: Bootstrapping dev account..."
DEV_ROLE_ARN=$(aws-vault exec "$DEV_PROFILE" -- "${SCRIPT_DIR}/bootstrap_account.sh" \
  --environment dev \
  --github-org "$GITHUB_ORG" \
  --github-repo "$GITHUB_REPO" \
  --region "$REGION" | extract_role_arn)
DEV_ACCOUNT_ID=$(extract_account_id_from_arn "$DEV_ROLE_ARN")
log_success "Dev account bootstrapped (role: $DEV_ROLE_ARN)"
echo

# --- Step 3: Bootstrap shared account (after prod/dev so account IDs are known) ---
log_info "Step 3/4: Bootstrapping shared account..."
SHARED_ROLE_ARN=$(aws-vault exec "$SHARED_PROFILE" -- "${SCRIPT_DIR}/bootstrap_account.sh" \
  --environment shared \
  --github-org "$GITHUB_ORG" \
  --github-repo "$GITHUB_REPO" \
  --prod-account-id "$PROD_ACCOUNT_ID" \
  --dev-account-id "$DEV_ACCOUNT_ID" \
  --region "$REGION" | extract_role_arn)
SHARED_ACCOUNT_ID=$(extract_account_id_from_arn "$SHARED_ROLE_ARN")
log_success "Shared account bootstrapped (role: $SHARED_ROLE_ARN)"
echo

# --- Step 4: Configure GitHub environments ---
if [[ "$SKIP_GITHUB" == "true" ]]; then
  log_warning "Step 4/4: Skipping GitHub environment configuration (--skip-github)"
else
  log_info "Step 4/4: Configuring GitHub environments..."
  "${SCRIPT_DIR}/configure_github.sh" \
    --repo "${GITHUB_ORG}/${GITHUB_REPO}" \
    --shared-account-id "$SHARED_ACCOUNT_ID" \
    --prod-account-id "$PROD_ACCOUNT_ID" \
    --dev-account-id "$DEV_ACCOUNT_ID" \
    --region "$REGION"
fi

# --- Summary ---
echo
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Bootstrap Complete${NC}"
echo -e "${GREEN}========================================${NC}"
echo
echo -e "${BLUE}OIDC Role ARNs:${NC}"
echo "  shared: $SHARED_ROLE_ARN"
echo "  prod:   $PROD_ROLE_ARN"
echo "  dev:    $DEV_ROLE_ARN"
echo

# --- Terraform import commands ---
echo -e "${BLUE}Next steps — run these Terraform import commands:${NC}"
echo

# Get OIDC provider ARNs from the role ARNs (same account, predictable format)
for env in shared prod dev; do
  case "$env" in
    shared) account_id="$SHARED_ACCOUNT_ID" ;;
    prod) account_id="$PROD_ACCOUNT_ID" ;;
    dev) account_id="$DEV_ACCOUNT_ID" ;;
  esac

  oidc_provider_arn="arn:aws:iam::${account_id}:oidc-provider/token.actions.githubusercontent.com"

  echo "# In terraform/environments/${env}/:"
  echo "terraform import module.github_oidc.aws_iam_openid_connect_provider.github[0] ${oidc_provider_arn}"
  echo "terraform import module.github_oidc.aws_iam_role.github_actions terramedic-github-actions-${env}"
  echo
done
