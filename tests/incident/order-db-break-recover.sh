#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8080}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
INCIDENT_FILE="${INCIDENT_FILE:-docker-compose.incident.yml}"

echo "Incident simulation: break order-service database connectivity"

docker compose -f "$COMPOSE_FILE" -f "$INCIDENT_FILE" up -d --force-recreate order-service

echo "Waiting for order-service incident signal"
sleep 15

set +e
incident_code="$(curl -sS -o /tmp/order-incident-response.txt -w "%{http_code}" "${BASE_URL}/orders/health")"
set -e

echo "order-service health during incident: HTTP ${incident_code}"

echo "Recovering order-service"
docker compose -f "$COMPOSE_FILE" up -d --force-recreate order-service

echo "Waiting for recovery"
sleep 20

recovery_code="$(curl -sS -o /tmp/order-recovery-response.txt -w "%{http_code}" "${BASE_URL}/orders/health")"

if [ "$recovery_code" != "200" ]; then
  echo "Recovery failed: order-service returned HTTP ${recovery_code}"
  cat /tmp/order-recovery-response.txt || true
  exit 1
fi

echo "Recovery successful: order-service returned HTTP 200"
