#!/usr/bin/env sh

SCRIPT_DIR=`dirname "$(readlink -f "$0")"`
PROJECT_DIR=`dirname "${SCRIPT_DIR}"`

#IMAGE_NAME=d6jyahgwk/mqtt_to_broadlink # 'official' image
IMAGE_NAME=mqtt_to_broadlink  # locally built image
IMAGE_TAG=latest

docker run --rm -d \
  --name "mqtt_to_broadlink" \
  -v "${PROJECT_DIR}/data/:/service/data/" \
  ${IMAGE_NAME}:${IMAGE_TAG}
