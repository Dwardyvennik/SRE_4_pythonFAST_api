#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
timestamp="$(date '+%Y-%m-%d %H:%M:%S %Z')"
exit_code=0

echo "============================================================"
echo "Combined SRE Troubleshooting Report"
echo "Timestamp: ${timestamp}"
echo "============================================================"
echo

"${SCRIPT_DIR}/check-logs.sh" || exit_code=1
echo
"${SCRIPT_DIR}/check-restarts.sh" || exit_code=1

echo
echo "================================================------------"
if [ "${exit_code}" -eq 0 ]; then
  echo "Combined result: OK"
else
  echo "Combined result: WARNING - review the report above."
fi
echo "============================================================"

exit "${exit_code}"
