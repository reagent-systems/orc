#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! python3 -c "import venv, ensurepip" 2>/dev/null; then
  sudo apt-get update -qq
  sudo apt-get install -y python3.12-venv
fi

install_into() {
  local venv_dir="$1"
  python3 -m venv "$venv_dir"
  "$venv_dir/bin/pip" install -U pip
  if [ -f gauntlet/requirements.txt ]; then
    "$venv_dir/bin/pip" install -r gauntlet/requirements.txt
  else
    "$venv_dir/bin/pip" install textual==2.1.2 rich==14.1.0 pytest==8.4.1
  fi
}

# Durable path: Cloud Agent git checkout can wipe workspace .venv.
install_into "${HOME}/.orc-venv"

# Local convenience for this checkout.
install_into .venv
