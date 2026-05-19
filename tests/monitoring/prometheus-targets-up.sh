#!/usr/bin/env bash
set -euo pipefail

PROM_URL="${PROM_URL:-http://localhost:9091}"

python3 - "$PROM_URL" <<'PY'
import json
import sys
import urllib.parse
import urllib.request

prom_url = sys.argv[1].rstrip("/")
query = urllib.parse.quote("up")
url = f"{prom_url}/api/v1/query?query={query}"

with urllib.request.urlopen(url, timeout=10) as response:
    payload = json.loads(response.read().decode("utf-8"))

if payload.get("status") != "success":
    print("Prometheus query failed")
    print(json.dumps(payload, indent=2))
    sys.exit(1)

results = payload.get("data", {}).get("result", [])
if not results:
    print("No Prometheus up targets returned")
    sys.exit(1)

failed = []
for item in results:
    metric = item.get("metric", {})
    value = item.get("value", ["", "0"])[1]
    name = metric.get("job") or metric.get("instance") or json.dumps(metric)
    if value != "1":
        failed.append(name)

if failed:
    print("DOWN targets:")
    for name in failed:
        print(f"- {name}")
    sys.exit(1)

print("All Prometheus targets are UP")
for item in results:
    metric = item.get("metric", {})
    print(f"- {metric.get('job', metric.get('instance', 'unknown'))}")
PY
