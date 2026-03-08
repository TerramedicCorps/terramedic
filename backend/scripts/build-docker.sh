#!/bin/bash

# Build and push Docker images for Lambda deployment

set -e

AWS_REGION=${AWS_REGION:-us-east-1}

AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$AWS_ACCOUNT}

if [ -z "$AWS_ACCOUNT_ID" ]; then
  echo "[ERROR] AWS_ACCOUNT_ID environment variable is not set" >&2
  exit 1
fi

ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

cd "$(dirname "$0")/.." || exit 1

build_geolambda() {
  echo "[INFO] Building geolambda base image with GDAL/GEOS/PROJ..."
  echo "[WARN] This will take 20-30 minutes for the first build"

  aws ecr describe-repositories --repository-names geolambda --region "${AWS_REGION}" 2>/dev/null ||
    aws ecr create-repository --repository-name geolambda --region "${AWS_REGION}"

  docker build \
    -f docker/geolambda/Dockerfile \
    -t geolambda:3.12.2 \
    --platform linux/amd64 \
    .

  docker tag geolambda:3.12.2 "${ECR_REGISTRY}/geolambda:3.12.2"
  docker tag geolambda:3.12.2 "${ECR_REGISTRY}/geolambda:latest"

  aws ecr get-login-password --region "${AWS_REGION}" |
    docker login --username AWS --password-stdin "${ECR_REGISTRY}"

  docker push "${ECR_REGISTRY}/geolambda:3.12.2"
  docker push "${ECR_REGISTRY}/geolambda:latest"

  echo "[INFO] Geolambda base image built and pushed successfully"
}

build_app() {
  local ENV=${1:-prod}
  echo "[INFO] Building application image for ${ENV} environment..."

  if [[ ! "$ENV" =~ ^(dev|prod)$ ]]; then
    echo "[ERROR] Invalid environment: $ENV. Must be dev or prod" >&2
    exit 1
  fi

  aws ecr describe-repositories --repository-names "terramedic-${ENV}" --region "${AWS_REGION}" 2>/dev/null ||
    aws ecr create-repository --repository-name "terramedic-${ENV}" --region "${AWS_REGION}"

  if ! docker image inspect geolambda:3.12.2 >/dev/null 2>&1; then
    echo "[WARN] Geolambda base image not found locally, pulling from ECR..."
    aws ecr get-login-password --region "${AWS_REGION}" |
      docker login --username AWS --password-stdin "${ECR_REGISTRY}"
    docker pull "${ECR_REGISTRY}/geolambda:3.12.2"
    docker tag "${ECR_REGISTRY}/geolambda:3.12.2" geolambda:3.12.2
  fi

  docker build \
    -f docker/lambda/Dockerfile \
    -t "terramedic-${ENV}:latest" \
    --platform linux/amd64 \
    --build-arg ECR_REGISTRY="${ECR_REGISTRY}" \
    .

  docker tag "terramedic-${ENV}:latest" "${ECR_REGISTRY}/terramedic-${ENV}:latest"

  TIMESTAMP=$(date +%Y%m%d-%H%M%S)
  docker tag "terramedic-${ENV}:latest" "${ECR_REGISTRY}/terramedic-${ENV}:${TIMESTAMP}"

  aws ecr get-login-password --region "${AWS_REGION}" |
    docker login --username AWS --password-stdin "${ECR_REGISTRY}"

  docker push "${ECR_REGISTRY}/terramedic-${ENV}:latest"
  docker push "${ECR_REGISTRY}/terramedic-${ENV}:${TIMESTAMP}"

  echo "[INFO] Application image for ${ENV} built and pushed successfully"
  echo "[INFO] Image URI: ${ECR_REGISTRY}/terramedic-${ENV}:latest"
}

case "${1}" in
  geolambda)
    build_geolambda
    ;;
  dev|prod)
    build_app "$1"
    ;;
  *)
    echo "Usage: $0 {geolambda|dev|prod}"
    exit 1
    ;;
esac
