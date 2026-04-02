#!/usr/bin/env bash
# Start the API locally. Run from the backend/ directory:
#   chmod +x run_dev.sh && ./run_dev.sh
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -d .venv ]]; then
  echo "Creating virtualenv .venv ..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -r requirements.txt
exec uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
