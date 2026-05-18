#!/usr/bin/env bash
set -e

PROJECT_NAME="sre6"
LEGACY_PROJECT_NAME="fastapi-microservices-master"

echo "Stopping old stack..."
docker compose -p "$PROJECT_NAME" down --remove-orphans || true
docker compose -p "$LEGACY_PROJECT_NAME" down --remove-orphans || true

echo "Starting stack..."
docker compose -p "$PROJECT_NAME" up -d --build

echo "Current status:"
docker compose -p "$PROJECT_NAME" ps
