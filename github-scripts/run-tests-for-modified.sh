#!/usr/bin/env bash
# Script to run pytest for tests corresponding to modified Python modules in src/

# Ensure project root is on PYTHONPATH so src/ is importable
export PYTHONPATH="$(git rev-parse --show-toplevel)"

git diff --cached --name-only --diff-filter=AM | grep '^src/.*\.py$' | while read file; do
    module=$(basename "$file" .py)
    test_file="tests/test_${module}.py"
    if [ -f "$test_file" ]; then
        echo "Running tests for $test_file..."
        pytest "$test_file" || exit 1
    fi
done
