#!/usr/bin/env bash
#
# Builds the local NeMo Guardrails images:
#   1. Clones the upstream NeMo Guardrails repository at a pinned tag and
#      builds its Dockerfile as `nemoguardrails:base`.
#   2. Builds this repo's overlay image (Dockerfile.overlay) FROM that base,
#      tagged as `nvidia-nemo-guardrails:local` (override with IMAGE_TAG).
#
# Requires: docker (with BuildKit), git, network access.

set -euo pipefail

# Pinned upstream version (edit to upgrade).
NEMO_GUARDRAILS_TAG="${NEMO_GUARDRAILS_TAG:-v0.23.0}"
UPSTREAM_REPO="https://github.com/NVIDIA-NeMo/Guardrails.git"
BUILD_DIR="${BUILD_DIR:-$(mktemp -d)/nemoguardrails-upstream}"
BASE_IMAGE="${BASE_IMAGE:-nemoguardrails:base}"
OVERLAY_IMAGE="${OVERLAY_IMAGE:-nvidia-nemo-guardrails:local}"

echo "==> Cloning upstream NeMo Guardrails at ${NEMO_GUARDRAILS_TAG}"
rm -rf "${BUILD_DIR}"
git clone --depth 1 --branch "${NEMO_GUARDRAILS_TAG}" "${UPSTREAM_REPO}" "${BUILD_DIR}"

echo "==> Building base image (${BASE_IMAGE}) from upstream Dockerfile"
docker build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  -t "${BASE_IMAGE}" \
  "${BUILD_DIR}"

echo "==> Building overlay image (${OVERLAY_IMAGE})"
docker build \
  --build-arg NEMOGUARDRAILS_IMAGE="${BASE_IMAGE}" \
  -t "${OVERLAY_IMAGE}" \
  -f Dockerfile.overlay \
  .

echo "==> Done."
echo "    Run locally:  docker compose up guardrails"
echo "    Overlay:      ${OVERLAY_IMAGE}"
echo "    Base:         ${BASE_IMAGE}"
