#!/bin/bash

SERVER_LOGS="/home/ec2-user/prefect_logs/server-compose.log"
AGENT_LOGS="/home/ec2-user/prefect_logs/agent.log"
TOKEN=`curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"` 
INSTANCE_ID=`curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id`
EC2_IP=`curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/local-ipv4`
EC2_AVAIL_ZONE=`curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone`
REGION_NAME="`echo \"$EC2_AVAIL_ZONE\" | sed 's/[a-z]$//'`"

echo Prefect Server compose start
echo "** nohupping prefect server start"
echo "** Instance id is ${INSTANCE_ID}"
echo "** Instance ip is ${EC2_IP}"
echo "** logs can be found in ${SERVER_LOGS}"
echo "** logrotate configuration located in /etc/logrotate.d/prefect_server_logs"
echo "** cron set to invoke logrotate every minute as per /etc/cron.d/prefect-logrotate"
echo "** Cloudwatch logs going to /prefect/server-compose/${INSTANCE_ID} as per /etc/awslogs/awslogs.conf"

export PREFECT__FLOWS__CHECKPOINTING=true
export PREFECT__TASKS__CHECKPOINTING=true
export PREFECT__FLOWS__DEFAULTS__STORAGE__DEFAULT_CLASS=prefect.engine.results.PrefectResult


nohup prefect server start | grep -v hasura > ${SERVER_LOGS} 2>&1 &

echo Prefect agent start
echo "** Giving the server a little room to start (15 s)"
sleep 15
./start_prefect_agent.sh
