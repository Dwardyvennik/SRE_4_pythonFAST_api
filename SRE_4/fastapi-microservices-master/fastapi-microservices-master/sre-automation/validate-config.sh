#!/usr/bin/env bash
set -u

ENV_FILE="${ENV_FILE:-.env}"
REQUIRED_VARS=(
  "POSTGRES_DB"
  "POSTGRES_USER"
  "POSTGRES_PASSWORD"
  "DATABASE_URL"
  "JWT_SECRET"
  "JWT_ALGORITHM"
  "TOKEN_EXPIRE_MINUTES"
)

errors=0

echo "============================================================"
echo "SRE Pre-Deployment Configuration Validation"
echo "Environment file: ${ENV_FILE}"
echo "============================================================"

if [ ! -f "${ENV_FILE}" ]; then
  echo "ERROR: ${ENV_FILE} does not exist."
  echo "Create it first: cp .env.example .env"
  exit 1
fi

get_env_value() {
  local key="$1"
  grep -E "^[[:space:]]*${key}=" "${ENV_FILE}" | tail -n 1 | cut -d '=' -f 2- | sed 's/^["'\'']//; s/["'\'']$//'
}

for key in "${REQUIRED_VARS[@]}"; do
  value="$(get_env_value "${key}")"
  if [ -z "${value}" ]; then
    echo "ERROR: ${key} is missing or empty in ${ENV_FILE}."
    errors=1
  else
    echo "OK: ${key} is set."
  fi
done

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

token_expire_minutes="$(get_env_value "TOKEN_EXPIRE_MINUTES")"
if [ -n "${token_expire_minutes}" ] && ! echo "${token_expire_minutes}" | grep -Eq '^[0-9]+$'; then
  echo "ERROR: TOKEN_EXPIRE_MINUTES must be a positive integer."
  errors=1
fi

echo "================================================------------"
if [ "${errors}" -eq 0 ]; then
  echo "Configuration validation successful."
  echo "The environment is ready for Docker Compose deployment."
else
  echo "Configuration validation failed."
  exit 1
fi
echo "============================================================"
