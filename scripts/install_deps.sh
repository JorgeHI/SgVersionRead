#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
pip install -r "$ROOT/requirements.txt" --target "$ROOT/.deps/"
echo "Deps installed to $ROOT/.deps/"
