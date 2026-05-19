#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8080}"

endpoints=(
  "/auth/health"
  "/users/health"
  "/products/health"
  "/orders/health"
  "/notifications/health"
  "/chat/health"
)

echo "Smoke checks against ${BASE_URL}"

for endpoint in "${endpoints[@]}"; do
  url="${BASE_URL}${endpoint}"
  code="$(curl -sS -o /tmp/sre-smoke-response.txt -w "%{http_code}" "$url")"
  if [ "$code" != "200" ]; then
    echo "FAIL ${url} returned HTTP ${code}"
    cat /tmp/sre-smoke-response.txt || true
    exit 1
  fi
  echo "OK   ${url}"
done

echo "All service health checks passed"
