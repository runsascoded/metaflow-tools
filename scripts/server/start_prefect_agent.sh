#!/bin/bash

AGENT_LOGS="/home/ec2-user/prefect_logs/agent.log"
TOKEN=`curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"` 
EC2_AVAIL_ZONE=`curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone`
EC2_IP=`curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/local-ipv4`
REGION_NAME="`echo \"$EC2_AVAIL_ZONE\" | sed 's/[a-z]$//'`"
export PREFECT__USER_CONFIG_PATH=.prefect/local_agent_config.toml

echo Prefect agent start
echo "** nohupping prefect agent start"
echo "** local agent configuration in ${PREFECT__USER_CONFIG_PATH}"
echo "** logs can be found in ${AGENT_LOGS}"
echo "** logrotate configuration located in /etc/logrotate.d/prefect_agent_logs"
echo "** cron set to invoke logrotate every minute as per /etc/cron.d/prefect-logrotate"
echo "** Cloudwatch logs going to /prefect/agent/${INSTANCE_ID} as per /etc/awslogs/awslogs.conf"

# Start agent in container
IMAGE_NAME=rightsize_99_standard_py37
CONTAINER_NAME=prefect_agent

echo Authenticating with ECR
$(aws ecr get-login --no-include-email --region us-east-1)
AWS_ACCOUNT_NUMBER=386834949250
docker pull "${AWS_ACCOUNT_NUMBER}.dkr.ecr.us-east-1.amazonaws.com/${IMAGE_NAME}:gdesmarais"

docker kill ${CONTAINER_NAME} > /dev/null 2>&1
docker rm ${CONTAINER_NAME} > /dev/null 2>&1

# Run the agent through a command line startup
nohup docker run \
 	--env PREFECT__CLOUD__GRAPHQL="http://${EC2_IP}:4200/graphql" \
 	--env PREFECT__CLOUD__API="http://${EC2_IP}:4200" \
 	--env PREFECT__BACKEND=server \
 	--rm \
 	--entrypoint prefect \
 	--name ${CONTAINER_NAME} \
 	386834949250.dkr.ecr.us-east-1.amazonaws.com/${IMAGE_NAME}:gdesmarais \
 	agent start >> ${AGENT_LOGS} 2>&1 &
