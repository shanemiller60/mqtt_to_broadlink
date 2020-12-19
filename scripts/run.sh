#!/usr/bin/env sh

SCRIPT_DIR=`dirname "$(readlink -f "$0")"`
PROJECT_DIR=`dirname "${SCRIPT_DIR}"`

cd ${PROJECT_DIR}
PYTHONPATH=. python3 src/main.py

