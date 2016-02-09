#!/bin/sh

chown elasticsearch:elasticsearch /usr/share/elasticsearch/data

python /src/join_cluster.py

while :
do
	sleep 1
done

