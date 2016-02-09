import json
import os
import time
from httplib2 import Http


# create an glusterfs endpoint
os.system("kubectl create -f glusterfs-endpoints.json")

# create an glusterfs service
os.system("kubectl create -f glusterfs-service.json --validate=false")

# create an etcd endpoint
os.system("kubectl create -f etcd-endpoints.json")

# create an etcd service
os.system("kubectl create -f etcd-service.json --validate=false")

# create an etcd endpoint
os.system("kubectl create -f kubeapi-endpoints.json")

# create an etcd service
os.system("kubectl create -f kubeapi-service.json --validate=false")

# create a replication controller to replicate nodes
os.system("kubectl create -f cloudone-controller-glusterfs.json")

# create a service 
os.system("kubectl create -f cloudone-service.json")


