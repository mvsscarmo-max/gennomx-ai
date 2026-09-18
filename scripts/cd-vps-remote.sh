#!/bin/bash
# Pull GHCR images, retag to the live local names, recreate edge services only.
# Never down. Never -v. Never touch gennomx-ai-app Redis or postgres-ready.
set -euo pipefail

: "${GHCR_TOKEN:?}"
: "${GHCR_USER:?}"
: "${BACKEND_IMAGE:?}"
: "${FRONTEND_IMAGE:?}"
: "${IMAGE_TAG:?}"

EDGE=/docker/gennomx-ai-edge
test -f "$EDGE/docker-compose.yml"

echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USER" --password-stdin
docker pull "${BACKEND_IMAGE}:${IMAGE_TAG}"
docker pull "${FRONTEND_IMAGE}:${IMAGE_TAG}"
docker logout ghcr.io >/dev/null

docker tag "${BACKEND_IMAGE}:${IMAGE_TAG}" gennomx-ai-api-current:edge
docker tag "${FRONTEND_IMAGE}:${IMAGE_TAG}" gennomx-ai-frontend:edge

docker compose -p gennomx-ai-edge -f "$EDGE/docker-compose.yml" \
  up -d --no-deps --no-build --force-recreate api frontend worker beat

docker inspect gennomx-ai-api --format '{{.State.Status}}'
docker inspect gennomx-ai-frontend --format '{{.State.Status}}'
echo "cd-vps ai-edge ok $(date -u +%Y-%m-%dT%H:%M:%SZ)"
