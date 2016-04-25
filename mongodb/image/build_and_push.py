import json
import os
import time
from httplib2 import Http


os.system("sudo docker build -t cloudawan/mongodb src")
os.system("sudo docker push cloudawan/mongodb")


