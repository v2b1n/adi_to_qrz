#!/bin/bash
set -e
set -o pipefail

echo "$(date): running flake8"
flake8

echo "$(date): running pylint"
pylint *.py --errors-only
