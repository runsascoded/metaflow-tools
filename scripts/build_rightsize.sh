#!/usr/bin/env bash

#echo If prompted for credentials, enter the following information:
#echo "    Username: \$oauthtoken"
#echo "    Password: NTY4cDNjbTJjcjc2c29uaTBhaGdtMjQzcGk6ZTJkNTdmNWItMWI2MC00NjQ2LWI1OWMtZTIxNzlkMjRiNjBk"
#echo ---------------------------
CWD=$(pwd)
PID=$$
PYV=37

RED="\033[0;31m"
GREEN="\033[0;32m"
NC="\033[0m"

if [[ -f ".dockerignore" ]]; then
    echo Backing up existing .dockerignore
    cp .dockerignore .dockerignore.${PID}
fi

# We want to ignore the private dependencies during the base image builds
echo private-deps > .dockerignore

BASE_IMAGES=""
BASE_IMAGES="${BASE_IMAGES} rightsize_01_base_cuda102_py${PYV}"
BASE_IMAGES="${BASE_IMAGES} rightsize_02_conda${PYV}"
BASE_IMAGES="${BASE_IMAGES} rightsize_03_dask_base_py${PYV}"

for B in ${BASE_IMAGES}
do
  docker build -t celsiustx/${B} -f ../infrastructure/docker/${B}.dockerfile .
  RV=$?
  if [[ ${RV} != 0 ]]; then
    echo -e ${RED}Problem building image: ${B}${NC}
    exit 125
  fi
done

# This mode is going to use the develop branch for all the repos
if [ ! -e private-deps ]; then
  mkdir private-deps
fi

# Undo ignore of private-deps
echo "" > .dockerignore

CELSIUSTX_REPOS="celsius-utils multisample-analysis ctxbio cesium3 scannotate tumortate palantir phenograph"
# TODO - possibly expose different branch options here
BRANCH=develop
ALT_BRANCH=master

for R in ${CELSIUSTX_REPOS}
do
    if [[ -f ${R}/.dockerignore ]]; then
        echo Processing .dockerignore in ${R}
        while read p; do
            echo ${R}/${p} >> .dockerignore
        done<${R}/.dockerignore
    fi
    if [ ! -e private-deps/${R} ]; then
      git clone git@github.com:celsiustx/${R}.git -b ${BRANCH} private-deps/${R}
      RV=$?
      if [[ ${RV} != 0 ]]; then
        git clone git@github.com:celsiustx/${R}.git -b ${ALT_BRANCH} private-deps/${R}
        RV=$?
      fi
    else
      bash -c "cd private-deps/${R} && git checkout ${BRANCH} && git pull"
      RV=$?
      if [[ ${RV} != 0 ]]; then
        bash -c "cd private-deps/${R} && git checkout ${ALT_BRANCH} && git pull"
        RV=$?
      fi
    fi

    if [[ ${RV} != 0 ]]; then
      echo -e ${RED}Problem setting up private repo: ${R}${NC}
      exit 126
    fi
done


# Now build the final rightsize repo
IMAGE_NAME=rightsize_99_standard_py${PYV}
docker build --shm-size 256m -t celsiustx/${IMAGE_NAME} -f ../infrastructure/docker/${IMAGE_NAME}.dockerfile .
RV=$?

if [[ ${RV} == 0 ]]; then
    echo -e ${GREEN}Success, cleaning up${NC}
    rm .dockerignore
    if [[ -f ".dockerignore.${PID}" ]]; then
        echo Restoring previous .dockerignore
        mv .dockerignore.${PID} .dockerignore
    fi
else
    echo -e ${RED}Problem with build${NC}
    exit 1
fi



#
#bash -c "cd private-deps/celsius-utils; git pull"
#if [ ! -e ctxcommon ]; then
#  ln -s private-deps/celsius-utils/ctxcommon ctxcommon
#fi
#
#IMAGE_NAME=rightsize
#
#
#
##if [[ -z ${CTX_HOME} ]]; then
##    echo Please set CTX_HOME to the root of your repos.  It will be used as a temporory build environment
##    exit 1
##fi
#echo ""
#
#
##BUILD_DIR=$(mktemp -d ${CTX_HOME}/ctxbuild_temp_XXXXX)
#BUILD_DIR=${CTX_HOME}
#
#CWD=$(pwd)
#PID=$$
#
#cd ${BUILD_DIR}
#
#if [[ -f ".dockerignore" ]]; then
#    echo Backing up existing .dockerignore
#    cp .dockerignore .dockerignore.${PID}
#fi
#echo "" > .dockerignore
#
#RETAIN="celsius-utils multisample-analysis ctxbio cesium3 scannotate tumortate palantir phenograph"
#
#for fname in *; do
#    if [[ ${RETAIN} =~ ${fname} ]]; then
#        echo Including ${fname} in build context
#    else
#        echo ${fname} >> .dockerignore
#    fi
#done
#
#for R in ${RETAIN}
#do
#    if [[ -f ${R}/.dockerignore ]]; then
#        echo Processing .dockerignore in ${R}
#        while read p; do
##            echo adding ${R}/${p} to dockerignore
#            echo ${R}/${p} >> .dockerignore
#        done<${R}/.dockerignore
#    fi
#done
#
#INSTALL_REPOS="scannotate tumortate palantir phenograph"
#
## Get the external repo explicitly
#if [[ ! -d phenograph ]]; then
#    git clone git@github.com:jacoblevine/phenograph.git
#fi
#
#for R in ${INSTALL_REPOS}
#do
#    if [[ ! -d ${R} ]]; then
#        echo Cloning ${R}
#        git clone git@github.com:celsiustx/${R}.git
#    fi
#    if [[ -f ${R}/.dockerignore ]]; then
#        echo Processing .dockerignore in ${R}
#        while read p; do
#            echo ${R}/${p} >> .dockerignore
#        done<${R}/.dockerignore
#    fi
#done
#
#docker build --shm-size 256m -t ${IMAGE_NAME} -f multisample-analysis/infrastructure/docker/Dockerfile .
#RV=$?
#
#if [[ ${RV} == 0 ]]; then
#    echo Success, cleaning up
#    rm .dockerignore
#    if [[ -f ".dockerignore.${PID}" ]]; then
#        echo Restoring previous .dockerignore
#        mv .dockerignore.${PID} .dockerignore
#    fi
#else
#    echo Problem with build
#    exit 1
#fi
#
#cd ${CWD}
#

