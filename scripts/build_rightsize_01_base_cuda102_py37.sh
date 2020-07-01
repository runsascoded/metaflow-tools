#!/usr/bin/env bash

#echo If prompted for credentials, enter the following information:
#echo "    Username: \$oauthtoken"
#echo "    Password: NTY4cDNjbTJjcjc2c29uaTBhaGdtMjQzcGk6ZTJkNTdmNWItMWI2MC00NjQ2LWI1OWMtZTIxNzlkMjRiNjBk"
#echo ---------------------------

IMAGE_NAME=rightsize_base_cuda102_py37

docker build -t ${IMAGE_NAME} -f ../infrastructure/docker/${IMAGE_NAME}.dockerfile .
