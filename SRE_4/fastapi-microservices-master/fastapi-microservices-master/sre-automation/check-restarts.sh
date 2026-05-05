#!/usr/bin/env bash
set -u

SERVICES=(
  "auth-service"
  "product-service"
  "order-service"
  "postgres"
  "prometheus"
  "grafana"
)

timestamp="$(date '+%Y-%m-%d %H:%M:%S %Z')"
issues_found=0

echo "============================================================"
echo "SRE Container Restart Report"
echo "Timestamp: ${timestamp}"
echo "============================================================"

if ! docker compose version >/dev/null 2>&1; then
  echo "ERROR: docker compose is not available."
  exit 1
fi

defined_services="$(docker compose config --services 2>/dev/null || true)"

if ! docker compose ps >/dev/null 2>&1; then
  echo "ERROR: cannot access Docker containers for this Compose project."
  echo "Check that Docker is running and that your user can access the Docker daemon."
  exit 1
fi

for service in "${SERVICES[@]}"; do
  if ! echo "${defined_services}" | grep -Fxq "${service}"; then
    echo "WARNING: ${service} is not defined in the current Compose project."
    issues_found=1
    continue
  fi

  container_id="$(docker compose ps -q "${service}" 2>/dev/null || true)"

  if [ -z "${container_id}" ]; then
    echo "WARNING: ${service} is defined, but no container is currently created or running."
    issues_found=1
    continue
  fi

  restart_count="$(docker inspect --format '{{.RestartCount}}' "${container_id}" 2>/dev/null || echo "unknown")"

  if [ "${restart_count}" = "unknown" ]; then
    echo "WARNING: ${service} restart count could not be inspected."
    issues_found=1
  elif [ "${restart_count}" -gt 0 ]; then
    echo "WARNING: ${service} restarted ${restart_count} time(s)."
    issues_found=1
  else
    echo "OK: ${service} restart count is 0."
  fi
done

echo "================================================------------"
if [ "${issues_found}" -eq 0 ]; then
  echo "Overall result: OK - no container restarts detected."
else
  echo "Overall result: WARNING - one or more services restarted or are missing."
fi
echo "============================================================"
