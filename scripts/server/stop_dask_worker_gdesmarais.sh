#!/bin/bash

RED="\033[0;31m"
GREEN="\033[0;32m"
NC="\033[0m"

echo Killing dask worker containers
docker kill dask-worker-gdesmarais_1
docker kill dask-worker-gdesmarais_2
echo -e ${GREEN}All processes dead${NC}

