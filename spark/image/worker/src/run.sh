#!/bin/sh

unset SPARK_MASTER_PORT
unset SPARK_WORKER_PORT

/src/spark/sbin/start-slave.sh spark://$MASTER_SERVICE_NAME.$NAMESPACE.svc.cluster.local:7077

while :
do
	sleep 1
done

