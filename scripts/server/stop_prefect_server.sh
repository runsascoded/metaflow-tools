#!/bin/bash

RED="\033[0;31m"
GREEN="\033[0;32m"
NC="\033[0m"

# This doesn't work, and would need all the env vars set in the prefect/cli/server.py click interface
# I am keeping it because it would be a better solution
# YML_DIR="/home/ec2-user/prefect/server/docker"
# YML="${YML_DIR}/docker-compose.yml"
# echo docker-compose downing as per config in ${YML}
# cd ${YML_DIR}
# docker-compose down 

echo Killing prefect server processes:
echo 
ps -f | egrep "prefect|docker-compose" | grep -v grep | grep -v $0
pkill '^prefect$'
RV=$?
if [[ ${RV} != 0 ]]; then
  echo -e ${RED}Problem killing prefect - process not found${NC}
else
  echo
  echo Waiting for prefect process to give up
  ps -f | grep " prefect$" | grep -v grep
  RV=$?
  while [[ ${RV} == 0 ]]; do
    echo Giving a 5 second grace period
    sleep 5
    ps -f | grep " prefect$" | grep -v grep
    RV=$?
  done
  echo -e ${GREEN}Done waiting for prefect${NC}
fi

pkill '^docker-compose$'
RV=$?
if [[ ${RV} != 0 ]]; then
  echo -e ${RED}Problem killing docker-compose - process not found${NC}
else
  echo 
  echo Waiting for docker-compose processes to give up
  ps -f | grep " docker-compose up$" | grep -v grep
  RV=$?
  while [[ ${RV} == 0 ]]; do
    echo Giving a 5 second grace period
    sleep 5
    ps -f | grep " docker-compose up$" | grep -v grep
    RV=$?
  done
  echo -e ${GREEN}Done waiting for prefect${NC}
fi

echo -e ${GREEN}All processes dead${NC}

