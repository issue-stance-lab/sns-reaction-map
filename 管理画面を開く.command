#!/bin/zsh
set -eu

SCRIPT_DIR="${0:A:h}"
cd "$SCRIPT_DIR"
exec python3 scripts/build_admin_dashboard.py --serve
