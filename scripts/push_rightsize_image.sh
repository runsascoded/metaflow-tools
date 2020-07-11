#!/usr/bin/env bash

RED="\033[0;31m"
GREEN="\033[0;32m"
NC="\033[0m"

if [[ -z "$1" ]]; then
  echo -e ${RED} "Missing parameter: image"
  echo "Usage: $0 <image> [environment]"
  echo "    image, required - a rightsize image"
  echo "    environment, optional - a deployment environment, used in tagging the pushed image"
  echo -e {$NC}
  exit 1
else
  DEPLOYMENT_IMAGE=$1
fi

if [[ -n "$2" ]]; then
    DEPLOYMENT_ENV=$2
else
    DEPLOYMENT_ENV=$(whoami)
fi

echo Will tag with: ${DEPLOYMENT_ENV}


# ./build_${DEPLOYMENT_IMAGE}.sh
#if [[ $? != 0 ]]; then
#    echo -e ${RED}Problem building ${DEPLOYMENT_IMAGE} image${NC}
#    exit 1
#fi
docker tag celsiustx/${DEPLOYMENT_IMAGE}:latest 386834949250.dkr.ecr.us-east-1.amazonaws.com/${DEPLOYMENT_IMAGE}:${DEPLOYMENT_ENV}
echo Pushing ${DEPLOYMENT_IMAGE} with tag ${DEPLOYMENT_ENV} to ECR
$(aws ecr get-login --no-include-email --region us-east-1)
docker push 386834949250.dkr.ecr.us-east-1.amazonaws.com/${DEPLOYMENT_IMAGE}:${DEPLOYMENT_ENV}

echo -e ${GREEN}Done pushing ${DEPLOYMENT_IMAGE} with tag ${DEPLOYMENT_ENV} ${NC}
