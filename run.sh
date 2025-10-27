#!/usr/bin/env bash
set -euo pipefail

# Convenience launcher for Linux/macOS.
# Ensures the virtual environment is ready and runs a Python script inside it.
# Usage:
#   bash run.sh                    # runs testeMostraGrade.py by default
#   bash run.sh ARQUIVO.py [args]  # runs the given file inside the venv

TARGET=${1:-testeMostraGrade.py}
shift || true

# Delegate to the main environment setup helper
exec bash "$(dirname "$0")/setup_env.sh" run "$TARGET" "$@"
