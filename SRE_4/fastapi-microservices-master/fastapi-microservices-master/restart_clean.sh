#!/usr/bin/env bash
set -e

PORTS="8080|8081|9091|52057|5431|5433|5434"

echo "Killing stuck docker-proxy processes on project ports..."

PIDS=$(sudo ss -ltnp | grep -E ":($PORTS)" | grep "docker-proxy" | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | sort -u)

if [ -n "$PIDS" ]; then
  echo "Found docker-proxy PIDs: $PIDS"
  sudo kill -9 $PIDS || true
else
  echo "No stuck docker-proxy processes found."
fi

echo "Checking ports after cleanup..."
sudo ss -ltnp | grep -E ":($PORTS)" || true

echo "Starting Docker Compose..."
docker compose up -d --build --remove-orphans

echo "Status:"
docker compose ps
