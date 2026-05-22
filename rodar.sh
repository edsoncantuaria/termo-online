#!/usr/bin/env bash
set -euo pipefail

Raiz="$(cd "$(dirname "$0")" && pwd)"
cd "$Raiz"

if [[ ! -d .venv ]]; then
  echo "Criando ambiente virtual..."
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi

cd src
exec "$Raiz/.venv/bin/python3" main.py
