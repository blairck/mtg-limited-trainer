#!/bin/bash

# Run pre-commit hooks on all files
echo "Running Black formatter on all Python files..."
poetry run pre-commit run --all-files

echo "Done!"
