#!/bin/bash
# TODO - hook this up to cloudwatch

SCHEDULER_LOGS="/home/ec2-user/prefect_logs/dask_scheduler.log"
TOKEN=`curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"`
EC2_IP=`curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/local-ipv4`

echo Authenticating with ECR
$(aws ecr get-login --no-include-email --region us-east-1)


CONTAINER_NAME=dask-scheduler-cpu-gdesmarais
AWS_ACCOUNT_NUMBER=386834949250
IMAGE_NAME="${AWS_ACCOUNT_NUMBER}.dkr.ecr.us-east-1.amazonaws.com/rightsize_99_standard_py37:gdesmarais"
CONTAINER_PORT_A=8786
HOST_PORT_A=18786
CONTAINER_PORT_B=8787
HOST_PORT_B=18787

docker pull ${IMAGE_NAME}

echo Started Dask CPU scheduler
echo "**"
echo "** logs can be found in ${SCHEDULER_LOGS}"
echo "** logrotate configuration located in /etc/logrotate.d/dask_scheduler_log"
echo "** cron set to invoke logrotate every minute as per /etc/cron.d/prefect-logrotate"
echo "** Cloudwatch logs going to /prefect/dask_scheduler/${INSTANCE_ID} as per /etc/awslogs/awslogs.conf"
echo "**"
echo "** Container name: ${CONTAINER_NAME}"
echo "** Image name: ${IMAGE_NAME}"
echo "** Host Port A: ${HOST_PORT_A}"
echo "** Host Port B: ${HOST_PORT_B}"
echo "**"
echo "*** To connect to the Dask Scheduler Dashboard, visit http://${EC2_IP}:${HOST_PORT_B}"

docker kill ${CONTAINER_NAME} > /dev/null 2>&1
docker rm ${CONTAINER_NAME} > /dev/null 2>&1
nohup docker run \
    -p ${HOST_PORT_A}:${CONTAINER_PORT_A} \
    -p ${HOST_PORT_B}:${CONTAINER_PORT_B} \
    --name ${CONTAINER_NAME} ${IMAGE_NAME} \
    dask-scheduler >> ${SCHEDULER_LOGS} 2>&1 &

