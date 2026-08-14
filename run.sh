#!/bin/bash

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$PROJECT_DIR"

source "$PROJECT_DIR/venv/bin/activate"

exec python3 "$PROJECT_DIR/main.py"
