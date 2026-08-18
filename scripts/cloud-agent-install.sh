#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! python3 -c "import venv, ensurepip" 2>/dev/null; then
  sudo apt-get update -qq
  sudo apt-get install -y python3.12-venv
fi

python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -r gauntlet/requirements.txt
