#!/usr/bin/env bash
set -u

ENV_FILE="${ENV_FILE:-.env}"
EXAMPLE_FILE="${EXAMPLE_FILE:-.env.example}"
REQUIRED_VARS=(
  "POSTGRES_DB"
  "POSTGRES_USER"
  "POSTGRES_PASSWORD"
  "POSTGRES_PORT"
  "DATABASE_URL"
  "ORDER_DATABASE_URL"
  "PRODUCT_SERVICE_URL"
  "JWT_SECRET"
  "JWT_ALGORITHM"
  "TOKEN_EXPIRE_MINUTES"
  "HTTP_PORT"
  "PROMETHEUS_PORT"
  "GRAFANA_PORT"
  "GRAFANA_ADMIN_USER"
  "GRAFANA_ADMIN_PASSWORD"
  "AUTH_PORT"
  "PRODUCT_PORT"
)

errors=0

echo "============================================================"
echo "SRE Pre-Deployment Configuration Validation"
echo "Environment file: ${ENV_FILE}"
echo "Example file: ${EXAMPLE_FILE}"
echo "============================================================"

if [ ! -f "${ENV_FILE}" ]; then
  echo "ERROR: ${ENV_FILE} does not exist."
  echo "Create it first: cp .env.example .env"
  exit 1
fi

if [ ! -f "${EXAMPLE_FILE}" ]; then
  echo "ERROR: ${EXAMPLE_FILE} does not exist."
  errors=1
fi

get_env_value() {
  local key="$1"
  grep -E "^[[:space:]]*${key}=" "${ENV_FILE}" | tail -n 1 | cut -d '=' -f 2- | sed 's/^["'\'']//; s/["'\'']$//'
}

get_example_value() {
  local key="$1"
  if [ ! -f "${EXAMPLE_FILE}" ]; then
    return 0
  fi
  grep -E "^[[:space:]]*${key}=" "${EXAMPLE_FILE}" | tail -n 1 | cut -d '=' -f 2- | sed 's/^["'\'']//; s/["'\'']$//'
}

for key in "${REQUIRED_VARS[@]}"; do
  value="$(get_env_value "${key}")"
  example_value="$(get_example_value "${key}")"
  if [ -z "${example_value}" ]; then
    echo "ERROR: ${key} is missing or empty in ${EXAMPLE_FILE}."
    errors=1
  fi
  if [ -z "${value}" ]; then
    echo "ERROR: ${key} is missing or empty in ${ENV_FILE}."
    errors=1
  else
    echo "OK: ${key} is set."
  fi
done

is_port() {
  local value="$1"
  [ -n "${value}" ] && echo "${value}" | grep -Eq '^[0-9]+$' && [ "${value}" -ge 1 ] && [ "${value}" -le 65535 ]
}

database_url="$(get_env_value "DATABASE_URL")"
if [ -n "${database_url}" ]; then
  if echo "${database_url}" | grep -Eq '@postgres(:|/)|//[^/@]*postgres(:|/)'; then
    echo "OK: DATABASE_URL uses Docker Compose hostname 'postgres'."
  else
    echo "ERROR: DATABASE_URL must use Docker Compose hostname 'postgres'."
    echo "Current DATABASE_URL: ${database_url}"
    errors=1
  fi
fi

order_database_url="$(get_env_value "ORDER_DATABASE_URL")"
if [ -n "${order_database_url}" ]; then
  if echo "${order_database_url}" | grep -Eq '@postgres(:|/)|//[^/@]*postgres(:|/)'; then
    echo "OK: ORDER_DATABASE_URL uses Docker Compose hostname 'postgres'."
  else
    echo "ERROR: ORDER_DATABASE_URL must use Docker Compose hostname 'postgres' when configured."
    echo "Current ORDER_DATABASE_URL: ${order_database_url}"
    errors=1
  fi
fi

product_service_url="$(get_env_value "PRODUCT_SERVICE_URL")"
if [ -n "${product_service_url}" ]; then
  if [ "${product_service_url}" = "http://product-service:8000" ]; then
    echo "OK: PRODUCT_SERVICE_URL points to product-service on the Docker network."
  else
    echo "ERROR: PRODUCT_SERVICE_URL must be http://product-service:8000 for Docker Compose."
    echo "Current PRODUCT_SERVICE_URL: ${product_service_url}"
    errors=1
  fi
fi

jwt_secret="$(get_env_value "JWT_SECRET")"
if [ -z "${jwt_secret}" ]; then
  echo "ERROR: JWT_SECRET must not be empty."
  errors=1
elif [ "${jwt_secret}" = "change-me-in-production" ]; then
  echo "WARNING: JWT_SECRET uses the demo value. Change it for production."
fi

token_expire_minutes="$(get_env_value "TOKEN_EXPIRE_MINUTES")"
if [ -n "${token_expire_minutes}" ] && ! echo "${token_expire_minutes}" | grep -Eq '^[0-9]+$'; then
  echo "ERROR: TOKEN_EXPIRE_MINUTES must be a positive integer."
  errors=1
fi

PORT_VARS=(
  "POSTGRES_PORT"
  "HTTP_PORT"
  "PROMETHEUS_PORT"
  "GRAFANA_PORT"
  "AUTH_PORT"
  "PRODUCT_PORT"
)

for key in "${PORT_VARS[@]}"; do
  value="$(get_env_value "${key}")"
  if ! is_port "${value}"; then
    echo "ERROR: ${key} must be a valid TCP port number from 1 to 65535."
    errors=1
  else
    echo "OK: ${key} is a valid port."
  fi
done

echo "================================================------------"
if [ "${errors}" -eq 0 ]; then
  echo "Configuration validation successful."
  echo "The environment is ready for Docker Compose deployment."
else
  echo "Configuration validation failed."
  exit 1
fi
echo "============================================================"
