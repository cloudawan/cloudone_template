import json
import os
import time
from httplib2 import Http


#os.system("sudo docker build -t private-registry:31000/elasticsearch src")
#os.system("sudo docker push private-registry:31000/elasticsearch")
os.system("sudo docker build -t cloudawan/elasticsearch src")
os.system("sudo docker push cloudawan/elasticsearch")


