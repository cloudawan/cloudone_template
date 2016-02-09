__author__ = 'ycchang'


import sys
import json
import os
import time
import copy
from httplib2 import Http


class Utility:
    def __init__(self):
        pass

    @staticmethod
    def execute_until_timeout(function, timeout, *parameters):
        for counter in xrange(0, timeout+1):
            time.sleep(1)
            result = function(*parameters)
            # None is undecided
            if result is None:
                pass
            else:
                return result
        return False

            
class Glusterfs:
    def __init__(self):
        self.parameter_dictionary = {
            "application_name": None,
            "kubeapi_host_and_port": None,
            "namespace": None,
            "size": None,
            "service_file_name": None,
            "environment_file_name": None,
            "timeout_in_second": None,
            "action": None,
        }

        if self.__handle_input() is False:
            sys.exit(-1)
        else:
            print "Parameters are: " + str(self.parameter_dictionary)
    
        self.http = Http()
        
        self.application_name = self.parameter_dictionary.get("application_name", "name")
        self.kubeapi_host_and_port = self.parameter_dictionary.get("kubeapi_host_and_port", "http://127.0.0.1:8080")
        self.size = int(self.parameter_dictionary.get("size", 1))
        self.service_file_name = self.parameter_dictionary.get("service_file_name", "service.json")
        self.environment_file_name = self.parameter_dictionary.get("environment_file_name", "environment.json")
        self.time_to_wait = int(self.parameter_dictionary.get("timeout_in_second", 60))
        self.namespace = self.parameter_dictionary.get("namespace", "default")
        self.action = self.parameter_dictionary.get("action", "create")

        self.service_dictionary = self.__load_service_file()
        self.environment_pair_list = self.__load_environment_file()
   
        self.service_name = self.application_name
        self.endpoint_name = self.application_name

    def __handle_input(self):
        parameter_list = sys.argv[1:]
        for parameter in parameter_list:
            key_value = parameter[2:]
            key_value_list = key_value.split("=")
            self.parameter_dictionary[key_value_list[0]] = key_value_list[1]

        result = True
        for key, value in self.parameter_dictionary.iteritems():
            if value is None:
                print "Parameter " + key + " is missing"
                result = False

        return result

    def __load_service_file(self):
        with open(self.service_file_name, "r") as file_read:
            text = file_read.read()
            return json.loads(text)
        
    def __load_environment_file(self):
        with open(self.environment_file_name, "r") as file_read:
            text = file_read.read()
            return json.loads(text)

    def __create_endpoint(self):
        endpoint_dictionary = {
            "apiVersion": "v1",
            "kind": "Endpoints",
            "metadata": {
                "name": self.endpoint_name
            },
            "subsets": [
            ]
        }
        ip_list = []
        for environment_pair in self.environment_pair_list:
            if environment_pair.get("name") == "GLUSTERFS_IP_LIST":
                ip_list = environment_pair.get("value").split(",")
                for i in xrange(0, len(ip_list)):
                    ip_list[i] = ip_list[i].strip()
                break
        for ip in ip_list:
            endpoint_dictionary["subsets"].append({
                "addresses": [
                    {
                        "ip": ip
                    }
                ],
                "ports": [
                    {
                        "port": 40000
                    }
                ]
            })
        return endpoint_dictionary

    def __create_service(self):
        service_dictionary = copy.deepcopy(self.service_dictionary)
        service_dictionary["metadata"]["name"] = self.service_name
        
        return service_dictionary
        
    def create_cluster(self):
        # Create a endpoint
        self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace +
                          "/endpoints", "POST", json.dumps(self.__create_endpoint()))
        # Create a service
        self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace +
                          "/services", "POST", json.dumps(self.__create_service()))
        return True
    
    def clean_cluster(self):
        # Delete a endpoint
        self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace +
                          "/endpoints/" + self.endpoint_name, "DELETE")
        # Delete a service
        self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace +
                          "/services/" + self.service_name, "DELETE")
        return True

glusterfs = Glusterfs()
if glusterfs.action == "create":
    if not glusterfs.create_cluster():
        glusterfs.clean_cluster()
        sys.exit(-1)
elif glusterfs.action == "clean":
    glusterfs.clean_cluster()
else:
    print "No such action"
