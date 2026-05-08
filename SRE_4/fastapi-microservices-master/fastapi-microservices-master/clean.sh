#!/usr/bin/env bash
set -e

PROJECT_NAME="sre6"

echo "Stopping Docker stack..."
docker compose -p "$PROJECT_NAME" down --remove-orphans || true

echo "Removing leftover containers for this project..."
docker ps -a --filter "name=${PROJECT_NAME}-" -q | xargs -r docker rm -f

echo "Done."



