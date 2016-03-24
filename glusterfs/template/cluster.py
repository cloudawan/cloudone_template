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
    SUCEESS = 0
    ERROR_OTHER = 1
    ERROR_NO_SUCH_ACTION_SUPPORT = 2
    ERROR_NO_ACTION_PARAMETER = 3
    ERROR_PARAMETER_MISSING = 4
    ERROR_FAIL_TO_CREATE_ENDPOINT = 5
    ERROR_FAIL_TO_CREATE_SERVICE = 6
    ERROR_FAIL_TO_DELETE_SERVICE = 7
    ERROR_FAIL_TO_DELETE_ENDPOINT = 8

    def __init__(self):
        self.parameter_dictionary = self.__get_input()
        self.action = self.parameter_dictionary.get("action")
        if self.action == None:
            sys.exit(Glusterfs.ERROR_NO_ACTION_PARAMETER)

        if self.action == "create":
            self.parameter_list = [
                "application_name",
                "kubeapi_host_and_port",
                "namespace",
                "size",
                "service_file_name",
                "environment_file_name",
                "timeout_in_second",
                "action",
            ]
            if self.__check_input() is False:
                sys.exit(Glusterfs.ERROR_PARAMETER_MISSING)
            else:
                print "Parameters are: " + str(self.parameter_dictionary)

            self.__initialize_create()

        elif self.action == "delete":
            self.parameter_list = [
                "application_name",
                "kubeapi_host_and_port",
                "namespace",
                "timeout_in_second",
                "action",
            ]
            if self.__check_input() is False:
                sys.exit(Glusterfs.ERROR_PARAMETER_MISSING)
            else:
                print "Parameters are: " + str(self.parameter_dictionary)

            self.__initialize_delete()

    def __initialize_create(self):
        self.http = Http()

        self.application_name = self.parameter_dictionary.get("application_name")
        self.kubeapi_host_and_port = self.parameter_dictionary.get("kubeapi_host_and_port")
        self.size = int(self.parameter_dictionary.get("size"))
        self.service_file_name = self.parameter_dictionary.get("service_file_name")
        self.environment_file_name = self.parameter_dictionary.get("environment_file_name")
        self.time_to_wait = int(self.parameter_dictionary.get("timeout_in_second"))
        self.namespace = self.parameter_dictionary.get("namespace")
        self.action = self.parameter_dictionary.get("action")

        self.service_dictionary = self.__load_service_file()
        self.environment_pair_list = self.__load_environment_file()

        self.service_name = self.application_name
        self.endpoint_name = self.application_name

    def __initialize_delete(self):
        self.http = Http()

        self.application_name = self.parameter_dictionary.get("application_name")
        self.kubeapi_host_and_port = self.parameter_dictionary.get("kubeapi_host_and_port")
        self.time_to_wait = int(self.parameter_dictionary.get("timeout_in_second"))
        self.namespace = self.parameter_dictionary.get("namespace")
        self.action = self.parameter_dictionary.get("action")

        self.service_name = self.application_name
        self.endpoint_name = self.application_name

    def __get_input(self):
        parameter_dictionary = dict()
        parameter_list = sys.argv[1:]
        for parameter in parameter_list:
            key_value = parameter[2:]
            key_value_list = key_value.split("=")
            parameter_dictionary[key_value_list[0]] = key_value_list[1]
        return parameter_dictionary

    def __check_input(self):
        result = True
        for parameter in self.parameter_list:
            if self.parameter_dictionary.get(parameter) == None:
                print "Parameter " + parameter + " is missing"
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
        head, body = self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace +
                          "/endpoints", "POST", json.dumps(self.__create_endpoint()))

        if head.status != 201:
            print "Fail to create endpoint " + self.endpoint_name
            print head
            print body
            return Glusterfs.ERROR_FAIL_TO_CREATE_ENDPOINT

        # Create a service
        head, body = self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace +
                          "/services", "POST", json.dumps(self.__create_service()))

        if head.status != 201:
            print "Fail to create service " + self.service_name
            print head
            print body
            return Glusterfs.ERROR_FAIL_TO_CREATE_SERVICE

        return Glusterfs.SUCEESS

    def clean_cluster(self):
        # Delete a endpoint
        head, body = self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace +
                          "/endpoints/" + self.endpoint_name, "DELETE")

        if head.status != 200:
            print "Fail to delete endpoint " + self.endpoint_name
            print head
            print body
            return Glusterfs.ERROR_FAIL_TO_DELETE_ENDPOINT

        # Delete a service
        head, body = self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace +
                          "/services/" + self.service_name, "DELETE")

        if head.status != 200:
            print "Fail to delete service " + self.service_name
            print head
            print body
            return Glusterfs.ERROR_FAIL_TO_DELETE_SERVICE

        return Glusterfs.SUCEESS

glusterfs = Glusterfs()
if glusterfs.action == "create":
    status_code = glusterfs.create_cluster()
    if status_code != Glusterfs.SUCEESS: 
        glusterfs.clean_cluster()
        sys.exit(status_code)
elif glusterfs.action == "delete":
    status_code = glusterfs.clean_cluster()
    sys.exit(status_code)
else:
    print "No such action"
    sys.exit(Glusterfs.ERROR_NO_SUCH_ACTION_SUPPORT)
