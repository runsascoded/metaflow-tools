#!/usr/bin/env bash

#echo If prompted for credentials, enter the following information:
#echo "    Username: \$oauthtoken"
#echo "    Password: NTY4cDNjbTJjcjc2c29uaTBhaGdtMjQzcGk6ZTJkNTdmNWItMWI2MC00NjQ2LWI1OWMtZTIxNzlkMjRiNjBk"
#echo ---------------------------

if [[ -z ${CTX_HOME} ]]; then
    echo Please set CTX _HOME to the root of your local repos.
    exit 1
fi
if [[ -z ${CTX_BUILD_DIR} ]]; then
  me=`basename "$0"`
  CTX_BUILD_DIR=${HOME}/dev_build/${me}
  if [[ ! -e ${CTX_BUILD_DIR} ]]; then
    mkdir -p ${CTX_BUILD_DIR}
  fi
fi

if [[ -n "$1" ]]; then
    DEPLOYMENT_ENV=$1
else
    DEPLOYMENT_ENV=$(whoami)
    LOCAL_REPOS=true
fi

CWD=$(pwd)
PID=$$
PYV=37
MY_REPO_PATH=${CTX_HOME}/rightsize

RED="\033[0;31m"
GREEN="\033[0;32m"
NC="\033[0m"

BASE_IMAGES=""
BASE_IMAGES="${BASE_IMAGES} rightsize_01_base_cuda102_py${PYV}"
BASE_IMAGES="${BASE_IMAGES} rightsize_02_conda${PYV}"
BASE_IMAGES="${BASE_IMAGES} rightsize_03_dask_base_py${PYV}"

cp ${MY_REPO_PATH}/requirements.txt rightsize-requirements.txt
cp ${MY_REPO_PATH}/requirements-dask-base.txt requirements-dask-base.txt

for B in ${BASE_IMAGES}
do
  docker build -t celsiustx/${B} -f ../infrastructure/docker/${B}.dockerfile --build-arg FROM_TAG=${DEPLOYMENT_ENV} .
  RV=$?
  if [[ ${RV} != 0 ]]; then
    echo -e ${RED}Problem building image: ${B}${NC}
    exit 125
  fi
  ./push_rightsize_image.sh ${B} ${DEPLOYMENT_ENV}
done

# New work happens in the build dir
echo Build staging occuring in ${CTX_BUILD_DIR}
cd ${CTX_BUILD_DIR}

if [ ! -e private-deps ]; then
  mkdir private-deps
fi

# Undo ignore of private-deps
echo "" > .dockerignore

CELSIUSTX_REPOS="celsius-utils multisample-analysis ctxbio cesium3 rightsize scannotate tumortate palantir phenograph"
# TODO - possibly expose different branch options here
BRANCH=develop
ALT_BRANCH=master


for R in ${CELSIUSTX_REPOS}
do
  if [[ ${LOCAL_REPOS} == 'true' ]]; then
    if [[ -e ${CTX_HOME}/${R} ]]; then
      echo Staging ${R} from local source
      # shellcheck disable=SC2089
      echo $DEV_REPO_EXCLUDES
      # shellcheck disable=SC2090
      rsync -av ${CTX_HOME}/${R} private-deps \
        --exclude '.git' \
        --exclude '*venv' \
        --exclude '*node_modules' \
        --exclude 'private-deps' \
        --exclude 'doc' \
        --exclude 'docs' \
        --exclude 'service/.serverless' \
        --exclude '*test-env*' \
        --exclude '.idea'
#        --exclude 'test' \
#        --exclude 'tests' \
      continue
    fi
  fi
  if [ ! -e private-deps/${R} ]; then
    echo Cloning ${R} from ${BRANCH}
    git clone git@github.com:celsiustx/${R}.git -b ${BRANCH} private-deps/${R}
    RV=$?
    if [[ ${RV} != 0 ]]; then
      echo Trying instead ${R} from ${BRANCH}
      git clone git@github.com:celsiustx/${R}.git -b ${ALT_BRANCH} private-deps/${R}
      RV=$?
    fi
  else
    echo Checking out ${R} from ${BRANCH}
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
  if [[ -f ${R}/.dockerignore ]]; then
      echo Processing .dockerignore in ${R}
      while read p; do
          echo ${R}/${p} >> .dockerignore
      done<${R}/.dockerignore
  fi
done

# Now build the final rightsize repo
IMAGE_NAME=rightsize_99_standard_py${PYV}
echo Building Docker image ${IMAGE_NAME}

docker build --shm-size 256m -t celsiustx/${IMAGE_NAME} \
  -f ${MY_REPO_PATH}/infrastructure/docker/${IMAGE_NAME}.dockerfile \
  --build-arg FROM_TAG=${DEPLOYMENT_ENV} .
RV=$?
if [[ ${RV} != 0 ]]; then
  echo -e ${RED}Problem building image: ${IMAGE_NAME}${NC}
  exit 125
fi

${CWD}/push_rightsize_image.sh ${IMAGE_NAME} ${DEPLOYMENT_ENV}
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

