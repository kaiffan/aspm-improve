#!/usr/bin/env bash
set -euo pipefail
for tool in python3 kubectl helm; do
    command -v "$tool" >/dev/null || { echo "Missing required tool: $tool" >&2; exit 2; }
done
python3 -c 'import yaml' 2>/dev/null || { echo 'Install PyYAML in the active Python environment.' >&2; exit 2; }
exec python3 "$(dirname "$0")/deployment.py" rollback "$@"
