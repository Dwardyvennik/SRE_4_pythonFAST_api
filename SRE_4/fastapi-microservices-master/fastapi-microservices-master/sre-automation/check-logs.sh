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

PATTERN="error|failed|exception|database|connection refused|could not connect|timeout|restart|crash|panic"
LOG_LINES="${LOG_LINES:-200}"
timestamp="$(date '+%Y-%m-%d %H:%M:%S %Z')"
issues_found=0

echo "============================================================"
echo "SRE Log Troubleshooting Report"
echo "Timestamp: ${timestamp}"
echo "Log lines inspected per service: ${LOG_LINES}"
echo "Patterns: ${PATTERN}"
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
  echo
  echo "Service: ${service}"
  echo "------------------------------------------------------------"

  if ! echo "${defined_services}" | grep -Fxq "${service}"; then
    echo "WARNING: service is not defined in the current Compose project."
    issues_found=1
    continue
  fi

  if ! docker compose ps -q "${service}" 2>/dev/null | grep -q .; then
    echo "WARNING: ${service} is defined, but no container is currently created or running."
    issues_found=1
    continue
  fi

  matches="$(docker compose logs --no-color --tail "${LOG_LINES}" "${service}" 2>/dev/null | grep -Ein "${PATTERN}" || true)"

  if [ -n "${matches}" ]; then
    echo "SUSPICIOUS LOGS FOUND"
    echo "${matches}"
    issues_found=1
  else
    echo "OK: no suspicious log patterns found."
  fi
done

echo
echo "================================================------------"
if [ "${issues_found}" -eq 0 ]; then
  echo "Overall result: OK - no suspicious logs detected."
else
  echo "Overall result: WARNING - suspicious logs or missing containers detected."
fi
echo "============================================================"
