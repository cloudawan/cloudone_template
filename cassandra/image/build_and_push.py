import json
import os
import time
from httplib2 import Http


#os.system("sudo docker build -t private-registry:31000/cassandra src")
#os.system("sudo docker push private-registry:31000/cassandra")
os.system("sudo docker build -t cloudawan/cassandra src")
os.system("sudo docker push cloudawan/cassandra")


