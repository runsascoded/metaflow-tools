#!/bin/bash

IMAGE_NAME=rightsize_99_standard_py37


docker kill ${IMAGE_NAME} > /dev/null 2>&1
docker rm ${IMAGE_NAME} > /dev/null 2>&1
#docker run --rm --runtime=nvidia \
docker run --rm \
    -i -t --entrypoint /bin/bash \
    --name ${IMAGE_NAME} 386834949250.dkr.ecr.us-east-1.amazonaws.com/${IMAGE_NAME}:gdesmarais


