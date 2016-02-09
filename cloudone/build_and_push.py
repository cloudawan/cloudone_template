import json
import os
import time
from httplib2 import Http


os.system("sudo docker build -t cloudawan/cloudone cloudone")
os.system("sudo docker build -t cloudawan/cloudone_gui cloudone_gui")
os.system("sudo docker build -t cloudawan/cloudone_analysis cloudone_analysis")
os.system("sudo docker push cloudawan/cloudone")
os.system("sudo docker push cloudawan/cloudone_gui")
os.system("sudo docker push cloudawan/cloudone_analysis")


