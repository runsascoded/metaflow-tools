#!/bin/bash
. ${CTX_HOME}/execution-pipeline/scripts/read_aws_creds.sh 
read_aws_creds

IMAGE_NAME=$1

docker kill ${IMAGE_NAME} > /dev/null 2>&1
docker rm ${IMAGE_NAME} > /dev/null 2>&1
#docker run --rm --runtime=nvidia \
docker run --rm \
    -i -t --entrypoint /bin/bash \
    --env-file ~/aws_creds.env \
    --name ${IMAGE_NAME} celsiustx/${IMAGE_NAME}

