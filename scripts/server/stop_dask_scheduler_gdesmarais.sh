#!/bin/bash

RED="\033[0;31m"
GREEN="\033[0;32m"
NC="\033[0m"

echo Killing dask scheduler container
docker kill dask-scheduler-cpu-gdesmarais
docker kill dask-scheduler-gpu-gdesmarais
echo -e ${GREEN}All processes dead${NC}

