#!/bin/bash
set -e
set -o pipefail

echo "$(date): running flake8"
flake8

echo "$(date): running pylint"
pylint *.py --errors-only

# not yet ready
#echo "$(date): testing with python2"
#python2 ./adi_to_qrz.py --debug -x -i .testdata/test_log_1.adi
#
#echo "$(date): testing with python3"
#python3 ./adi_to_qrz.py --debug -x -i .testdata/test_log_2.adi
