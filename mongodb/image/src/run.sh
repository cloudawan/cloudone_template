#!/bin/sh

/usr/bin/mongod --config /etc/mongod.conf --bind_ip 0.0.0.0

while :
do
	sleep 1
done

