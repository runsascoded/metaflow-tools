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

# This can be retrieved with something like:
# aws ec2 describe-subnets --region=$REGION_NAME --region=$REGION_NAME --filters Name=vpc-id,Values=vpc-5eb4a127 | jq .Subnets[].SubnetId
# but I don't have the time to figure out the jq query to give me what I want
#        "Value": "Production App Subnet B",
#    "SubnetId": "subnet-a0a8539f",
#        "Value": "Production App Subnet A",
#    "SubnetId": "subnet-4f693443",
#        "Value": "Production App Subnet C",
#    "SubnetId": "subnet-0addbba2a743cc04e",


#export networkConfiguration="{'awsvpcConfiguration': {'assignPublicIp': 'DISABLED', 'subnets': ['subnet-4f693443', 'subnet-a0a8539f', 'subnet-0addbba2a743cc04e']}}"


#Fargate stuff - probably delete it
# python local_fargate_agent.py
#prefect agent start fargate -v --label s3-flow-storage --label fargate-task --label fargate-size-small
#nohup prefect agent start fargate --label s3-flow-storage --label fargate-task > ${AGENT_LOGS} 2>&1 &

#Generic agent start
# nohup prefect agent start --label s3-flow-storage >> ${AGENT_LOGS} 2>&1 &


# Start agent in container
IMAGE_NAME=rightsize_99_standard_py37
CONTAINER_NAME=prefect_agent
docker kill ${CONTAINER_NAME} > /dev/null 2>&1
docker rm ${CONTAINER_NAME} > /dev/null 2>&1
#docker run --rm \
#    -i -t --entrypoint /bin/bash \
#    --name ${IMAGE_NAME} 386834949250.dkr.ecr.us-east-1.amazonaws.com/${IMAGE_NAME}:gdesmarais

# Run the agent through a python startup
#docker run \
#	--env PREFECT__CLOUD__GRAPHQL="http://${EC2_IP}:4200/graphql" \
#	--env PREFECT__CLOUD__API="http://${EC2_IP}:4200" \
#	--env PREFECT__BACKEND=server \
#	--rm \
#	--entrypoint python \
#	--name ${CONTAINER_NAME} \
#	386834949250.dkr.ecr.us-east-1.amazonaws.com/${IMAGE_NAME}:gdesmarais \
#	-c 'print("hi");from prefect.agent.local.agent import LocalAgent;labels = ["s3-flow-storage"];LocalAgent(labels=labels).start()'

# Run the agent through a command line startup
docker run \
 	--env PREFECT__CLOUD__GRAPHQL="http://${EC2_IP}:4200/graphql" \
 	--env PREFECT__CLOUD__API="http://${EC2_IP}:4200" \
 	--env PREFECT__BACKEND=server \
 	--rm \
 	--entrypoint prefect \
 	--name ${CONTAINER_NAME} \
 	386834949250.dkr.ecr.us-east-1.amazonaws.com/${IMAGE_NAME}:gdesmarais \
 	agent start >> ${AGENT_LOGS} 2>&1 &