#!/usr/bin/env bash

IMAGE_NAME=mqtt_to_broadlink
IMAGE_TAG=0.1

SCRIPT_DIR=`dirname "$(readlink -f "$0")"`
ROOT_DIR=`dirname "${SCRIPT_DIR}"`
echo ${ROOT_DIR}

cd ${ROOT_DIR}
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -f ./docker/Dockerfile .

