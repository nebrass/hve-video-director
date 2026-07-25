#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1
bash -n scripts/check_requirements.sh
python3 -m unittest discover -s test/unit -p 'test_*.py'
