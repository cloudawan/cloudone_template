import json
import os
import time
from httplib2 import Http


#os.system("sudo docker build -t private-registry:31000/mariadb-galera src")
#os.system("sudo docker push private-registry:31000/mariadb-galera")
os.system("sudo docker build -t cloudawan/mariadb-galera src")
os.system("sudo docker push cloudawan/mariadb-galera")


