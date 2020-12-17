#!/usr/bin/env bash

IMAGE_NAME=mqtt_to_broadlink
IMAGE_TAG=0.1

docker run --rm -it \
  ${IMAGE_NAME}:${IMAGE_TAG}

#  --entrypoint=/bin/bash \
