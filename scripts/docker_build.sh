#!/usr/bin/env sh

IMAGE_NAME=mqtt_to_broadlink
IMAGE_TAG=latest

SCRIPT_DIR=`dirname "$(readlink -f "$0")"`
PROJECT_DIR=`dirname "${SCRIPT_DIR}"`

cd ${PROJECT_DIR}
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -f Dockerfile .

