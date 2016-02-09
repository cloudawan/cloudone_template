import json
import os
import time
from httplib2 import Http


#os.system("sudo docker build -t private-registry:31000/rabbitmq src")
#os.system("sudo docker push private-registry:31000/rabbitmq")
os.system("sudo docker build -t cloudawan/rabbitmq src")
os.system("sudo docker push cloudawan/rabbitmq")


