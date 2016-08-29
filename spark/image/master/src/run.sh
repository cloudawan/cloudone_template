#!/bin/sh

unset SPARK_MASTER_PORT
unset SPARK_WORKER_PORT

export SPARK_DAEMON_JAVA_OPTS="-Dspark.deploy.recoveryMode=FILESYSTEM -Dspark.deploy.recoveryDirectory=/var/lib/spark"

/src/spark/sbin/start-master.sh

while :
do
	sleep 1
done

