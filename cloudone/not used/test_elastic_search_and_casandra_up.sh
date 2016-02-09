#!/bin/bash

# Parameter
retry_amount=3
elastic_search_host="127.0.0.1"
elastic_search_port="9200"
cassandra_host="127.0.0.1"
cassandra_port="9042"

is_elastic_search_up() {
  elastic_search_url="http://$elastic_search_host:$elastic_search_port"
  elastic_search_response=$(curl "$elastic_search_url")

  if [[ $elastic_search_response == *"\"status\" : 200"* ]]
  then
    return 1
  else
    return 0
  fi
}

is_cassandra_up() {
  cassandra_url="http://$cassandra_host:$cassandra_port"
  cassandra_response=$(curl -m 1 "$cassandra_url")

  if [[ $cassandra_response == *"Invalid or unsupported protocol"* ]]
  then
    return 1
  else
    return 0
  fi
}

for ((i=0;i<$retry_amount;i++))
do
  echo "ping $i times to Elastic Search"
  is_elastic_search_up
  elastic_search_result=$?
  echo "ping $i times to Cassandra"
  is_cassandra_up
  cassandra_result=$?
  if [ $elastic_search_result == 1 ] && [ $cassandra_result == 1 ]; then
	break
  fi
  sleep 1
done

if [ $i == $retry_amount ]; then
  echo "Could not get ping response from Elastic Search or Cassandra"
  exit -1
fi
