#!/usr/bin/env sh

SCRIPT_DIR=`dirname "$(readlink -f "$0")"`
PROJECT_DIR=`dirname "${SCRIPT_DIR}"`

cd ${PROJECT_DIR}
python3 -m pip install -r requirements.txt

