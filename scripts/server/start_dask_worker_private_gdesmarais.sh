#!/bin/bash
# TODO - hook this up to cloudwatch

WORKER_LOGS="/home/ec2-user/prefect_logs/dask_worker_private_gdesmarais.log"
TOKEN=`curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"`
EC2_IP=`curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/local-ipv4`

echo Authenticating with ECR
$(aws ecr get-login --no-include-email --region us-east-1)


CONTAINER_NAME_1=dask-worker-private-gdesmarais_1
CONTAINER_NAME_2=dask-worker-private-gdesmarais_2
AWS_ACCOUNT_NUMBER=386834949250
IMAGE_NAME="${AWS_ACCOUNT_NUMBER}.dkr.ecr.us-east-1.amazonaws.com/rightsize_99_standard_py37:gdesmarais"
CONTAINER_PORT_A=8786
HOST_PORT_A=38786
CONTAINER_PORT_B=8787
HOST_PORT_B=38787

docker pull ${IMAGE_NAME}

echo Started Dask worker
echo "**"
echo "** logs can be found in ${WORKER_LOGS}"
echo "** logrotate configuration located in /etc/logrotate.d/dask_worker_log"
echo "** cron set to invoke logrotate every minute as per /etc/cron.d/prefect-logrotate"
echo "** Cloudwatch logs going to /prefect/agent/${INSTANCE_ID} as per /etc/awslogs/awslogs.conf"
echo "**"
echo "** Container name: ${CONTAINER_NAME}"
echo "** Image name: ${IMAGE_NAME}"
echo "** Host Port A: ${HOST_PORT_A}"
echo "** Host Port B: ${HOST_PORT_B}"
echo "**"
echo "*** To connect to the Dask Scheduler Dashboard, visit http://${EC2_IP}:${HOST_PORT_B}"

docker kill ${CONTAINER_NAME_1} > /dev/null 2>&1
docker rm ${CONTAINER_NAME_1} > /dev/null 2>&1
docker kill ${CONTAINER_NAME_2} > /dev/null 2>&1
docker rm ${CONTAINER_NAME_2} > /dev/null 2>&1
nohup docker run \
    --name ${CONTAINER_NAME_1} ${IMAGE_NAME} \
    dask-worker tcp://${EC2_IP}:${HOST_PORT_A} >> ${WORKER_LOGS} 2>&1 &
nohup docker run \
    --name ${CONTAINER_NAME_2} ${IMAGE_NAME} \
    dask-worker tcp://${EC2_IP}:${HOST_PORT_A} >> ${WORKER_LOGS} 2>&1 &

