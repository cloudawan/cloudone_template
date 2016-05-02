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


class Cluster:
    SUCEESS = 0
    ERROR_OTHER = 1
    ERROR_NO_SUCH_ACTION_SUPPORT = 2
    ERROR_NO_ACTION_PARAMETER = 3
    ERROR_PARAMETER_MISSING = 4
    ERROR_SIZE_LESS_THAN_ONE = 5
    ERROR_FAIL_TO_CREATE_REPLICATION_CONTROLLER = 6
    ERROR_FAIL_TO_GET_SEED_POD_NAME = 7
    ERROR_FAIL_TO_CREATE_SEED_INSTANCE = 8
    ERROR_FAIL_TO_CREATE_SERVICE = 9
    ERROR_FAIL_TO_CREATE_JOINING_INSTANCE = 10
    ERROR_FAIL_TO_GET_OWNING_REPLICATION_CONTROLLER_DATA = 11
    ERROR_FAIL_TO_PUT_OWNING_REPLICATION_CONTROLLER_DATA = 12
    ERROR_FAIL_TO_DELETE_SERVICE = 13
    ERROR_FAIL_TO_DELETE_REPLICATION_CONTROLLER = 14
    ERROR_FAIL_TO_DELETE_POD = 15

    def __init__(self):
        self.parameter_dictionary = self.__get_input()
        self.action = self.parameter_dictionary.get("action")
        if self.action == None:
            sys.exit(Cluster.ERROR_NO_ACTION_PARAMETER)

        if self.action == "create":
            self.parameter_list = [
                "application_name",
                "kubeapi_host_and_port",
                "namespace",
                "size",
                "service_file_name",
                "replication_controller_file_name",
                "environment_file_name",
                "timeout_in_second",
                "action",
            ]
            if self.__check_input() is False:
                sys.exit(Cluster.ERROR_PARAMETER_MISSING)
            else:
                print "Parameters are: " + str(self.parameter_dictionary)
                
            self.__initialize_create()

        elif self.action == "resize":
            self.parameter_list = [
                "application_name",
                "kubeapi_host_and_port",
                "namespace",
                "size",
                "replication_controller_file_name",
                "environment_file_name",
                "timeout_in_second",
                "action",
            ]
            if self.__check_input() is False:
                sys.exit(Cluster.ERROR_PARAMETER_MISSING)
            else:
                print "Parameters are: " + str(self.parameter_dictionary)

            self.__initialize_resize()

        elif self.action == "delete":
            self.parameter_list = [
                "application_name",
                "kubeapi_host_and_port",
                "namespace",
                "timeout_in_second",
                "action",
            ]
            if self.__check_input() is False:
                sys.exit(Cluster.ERROR_PARAMETER_MISSING)
            else:
                print "Parameters are: " + str(self.parameter_dictionary)

            self.__initialize_delete()
            
    def __initialize_create(self):
        self.http = Http()
        # Parameter
        self.application_name = self.parameter_dictionary.get("application_name") #name
        self.kubeapi_host_and_port = self.parameter_dictionary.get("kubeapi_host_and_port") #"http://127.0.0.1:8080
        self.namespace = self.parameter_dictionary.get("namespace") #default
        self.size = int(self.parameter_dictionary.get("size")) #3
        self.service_file_name = self.parameter_dictionary.get("service_file_name") #"service.json"
        self.replication_controller_file_name = self.parameter_dictionary.get("replication_controller_file_name") #"replication-controller.json"
        self.environment_file_name = self.parameter_dictionary.get("environment_file_name") #"environment.json"
        self.time_to_wait = int(self.parameter_dictionary.get("timeout_in_second")) #60 * 3
        self.action = self.parameter_dictionary.get("action") #create
        # File data
        self.replication_controller_dictionary = self.__load_replication_controller_file()
        self.service_dictionary = self.__load_service_file()
        # Indirect Data
        self.service_name = self.application_name #self.service_dictionary.get("metadata").get("name")
        self.replication_controller_name = self.application_name + "-instance" #self.replication_controller_dictionary.get("metadata").get("name")

    def __initialize_resize(self):
        self.http = Http()
        # Parameter
        self.application_name = self.parameter_dictionary.get("application_name") #name
        self.kubeapi_host_and_port = self.parameter_dictionary.get("kubeapi_host_and_port") #"http://127.0.0.1:8080
        self.namespace = self.parameter_dictionary.get("namespace") #default
        self.size = int(self.parameter_dictionary.get("size")) #3
        self.replication_controller_file_name = self.parameter_dictionary.get("replication_controller_file_name") #"replication-controller.json"
        self.environment_file_name = self.parameter_dictionary.get("environment_file_name") #"environment.json"
        self.time_to_wait = int(self.parameter_dictionary.get("timeout_in_second")) #60 * 3
        self.action = self.parameter_dictionary.get("action") #create
        # File data
        self.replication_controller_dictionary = self.__load_replication_controller_file()
        # Indirect Data
        self.service_name = self.application_name #self.service_dictionary.get("metadata").get("name")
        self.replication_controller_name = self.application_name + "-instance" #self.replication_controller_dictionary.get("metadata").get("name")

    def __initialize_delete(self):
        self.http = Http()
        # Parameter
        self.application_name = self.parameter_dictionary.get("application_name") #name
        self.kubeapi_host_and_port = self.parameter_dictionary.get("kubeapi_host_and_port") #"http://127.0.0.1:8080
        self.namespace = self.parameter_dictionary.get("namespace") #default
        self.time_to_wait = int(self.parameter_dictionary.get("timeout_in_second")) #60 * 3
        self.action = self.parameter_dictionary.get("action") #create
        # Indirect Data
        self.service_name = self.application_name #self.service_dictionary.get("metadata").get("name")
        self.replication_controller_name = self.application_name + "-instance" #self.replication_controller_dictionary.get("metadata").get("name")
        
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

    def __load_replication_controller_file(self):
        with open(self.replication_controller_file_name, "r") as file_read:
            text = file_read.read()
            return json.loads(text)

    def __load_service_file(self):
        with open(self.service_file_name, "r") as file_read:
            text = file_read.read()
            return json.loads(text)

    # Check seed instance
    def __check_seed_instance_up(self, pod_list):
        for pod in pod_list:
            head, body = self.http.request(
                self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace + "/pods/" + pod + "/log", "GET")
            for seed_instance_up_keyword in self.seed_instance_up_keyword_list:
                if seed_instance_up_keyword in body:
                    pass
                else:
                    return None
        return True

    # Check all instances are up in the cluster
    def __check_joining_instance_up(self, pod_list):
        for pod in pod_list:
            head, body = self.http.request(
                self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace + "/pods/" + pod + "/log", "GET")
            for all_instance_up_keyword in self.all_instance_up_keyword_list:
                if all_instance_up_keyword in body:
                    pass
                else:
                    return None
            for all_instance_failure_keyword in self.all_instance_failure_keyword_list:
                if all_instance_failure_keyword in body:
                    print body
                    return False
        return True

    # Check service is up
    def __check_service_up(self):
        head, body = self.http.request(
            self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace + "/services/" + self.service_name, "GET")
        if head.status == 200:
            return True
        else:
            return None

    # Get all instance name
    def __get_all_pod_name(self, expected_size=-1):
        pod_list = []
        head, body = self.http.request(
            self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace + "/pods/", "GET")
        dictionary = json.loads(body)
        for item in dictionary.get("items"):
            # Remove the pod name part -xxxxx
            name = item.get("metadata").get("name")[:-6]
            if name == self.replication_controller_name:
                pod_list.append(item.get("metadata").get("name"))

        if expected_size == -1 or expected_size == len(pod_list):
            return pod_list
        else:
            return None

    def __create_replication_controller(self):
        replication_controller_dictionary = copy.deepcopy(self.replication_controller_dictionary)
        replication_controller_dictionary["metadata"]["name"] = self.replication_controller_name
        replication_controller_dictionary["metadata"]["labels"]["name"] = self.replication_controller_name
        replication_controller_dictionary["spec"]["selector"]["name"] = self.service_name
        replication_controller_dictionary["spec"]["template"]["metadata"]["labels"]["name"] = self.service_name
        print replication_controller_dictionary
        return replication_controller_dictionary

    def __create_service(self):
        service_dictionary = copy.deepcopy(self.service_dictionary)
        service_dictionary["metadata"]["name"] = self.service_name
        service_dictionary["metadata"]["labels"]["name"] = self.service_name
        service_dictionary["spec"]["selector"]["name"] = self.service_name
        
        return service_dictionary
            
    def create_cluster(self):
        # Create a replication controller
        head, body = self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace +
                                       "/replicationcontrollers", "POST", json.dumps(self.__create_replication_controller()))
        if head.status != 201:
            print "Fail to create replication controller " + self.replication_controller_name
            print head
            print body
            return Cluster.ERROR_FAIL_TO_CREATE_REPLICATION_CONTROLLER

        # Get seed pod name
        seed_pod_list = Utility.execute_until_timeout(self.__get_all_pod_name, self.time_to_wait, 1)
        if seed_pod_list is False:
            print("Fail to get seed pod name")
            return Cluster.ERROR_FAIL_TO_GET_SEED_POD_NAME
        else:
            print("The created seed pod is:  " + str(seed_pod_list))

        # Check seed pod
        if Utility.execute_until_timeout(self.__check_seed_instance_up, self.time_to_wait, seed_pod_list):
            print("Successfully create the seed instance")
        else:
            print("Seed instance fail to come up")
            return Cluster.ERROR_FAIL_TO_CREATE_SEED_INSTANCE

        # Create a service to track all instances
        head, body = self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace +
                                       "/services", "POST", json.dumps(self.__create_service()))  
        if head.status != 201:
            print "Fail to create service " + self.service_name
            print head
            print body
            return Cluster.ERROR_FAIL_TO_CREATE_SERVICE
            
        # Check service
        if Utility.execute_until_timeout(self.__check_service_up, self.time_to_wait):
            print("Successfully create the service")
        else:
            print("Service fail to come up")
            return Cluster.ERROR_FAIL_TO_CREATE_SERVICE
            
        # Resize
        if self.size > 1:
            for i in xrange(1, self.size):
                result = self.resize_cluster(i + 1) 
                if result != Cluster.SUCEESS:
                    return result
            return Cluster.SUCEESS
        else:
            return Cluster.SUCEESS

    def clean_cluster(self):
        head, body = self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace + "/services/" +
                                       self.service_name, "DELETE")
        if head.status != 200:
            print "Fail to delete service " + self.service_name
            print head
            print body
            return Cluster.ERROR_FAIL_TO_DELETE_SERVICE
            
        head, body = self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace + "/replicationcontrollers/" +
                          self.replication_controller_name, "DELETE")
        if head.status != 200:
            print "Fail to delete replication controller " + self.replication_controller_name
            print head
            print body
            return Cluster.ERROR_FAIL_TO_DELETE_REPLICATION_CONTROLLER

        pod_list = self.__get_all_pod_name()
        for pod in pod_list:
            head, body = self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace + "/pods/" + pod, "DELETE")
            if head.status != 200:
                print "Fail to delete pod " + pod
                print head
                print body
                return Cluster.ERROR_FAIL_TO_DELETE_POD
        
        return Cluster.SUCEESS
                              
    def resize_cluster(self, size):
        # Get seed pod name
        seed_pod_list = Utility.execute_until_timeout(self.__get_all_pod_name, self.time_to_wait, size-1)
        if seed_pod_list is False:
            print("Fail to get seed pod name")
            return Cluster.ERROR_FAIL_TO_GET_SEED_POD_NAME
        else:
            print("The created seed pod is:  " + str(seed_pod_list))
            
        # Resize
        head, body = self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace +
                                       "/replicationcontrollers/" + self.replication_controller_name, "GET")
        if head.status != 200:
            print "Fail to get the current replication controller data"
            print head
            print body
            return Cluster.ERROR_FAIL_TO_GET_OWNING_REPLICATION_CONTROLLER_DATA

        replication_controller_dictionary = json.loads(body)
        replication_controller_dictionary["spec"]["replicas"] = size

        head, body = self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace +
                                       "/replicationcontrollers/" + self.replication_controller_name, "PUT",
                                       json.dumps(replication_controller_dictionary))
        if head.status != 200:
            print "Fail to put the new replication controller data"
            print head
            print body
            return Cluster.ERROR_FAIL_TO_PUT_OWNING_REPLICATION_CONTROLLER_DATA

        # Get all pod name
        pod_list = Utility.execute_until_timeout(self.__get_all_pod_name, self.time_to_wait, size)
        pod_without_seed_list = []
        for pod in pod_list:
            if pod in seed_pod_list:
                pass
            else:
                pod_without_seed_list.append(pod)
        print("The created pods are:  " + str(pod_without_seed_list))

        print("Waiting for internal synchronization")
        # Check for all instances
        if Utility.execute_until_timeout(self.__check_joining_instance_up, self.time_to_wait, pod_without_seed_list):
            print("Successfully resize the cluster")
            return Cluster.SUCEESS
        else:
            print("One or more instances fail to join the cluster")
            return Cluster.ERROR_FAIL_TO_CREATE_JOINING_INSTANCE

            
class Cassandra(Cluster):
    def __init__(self):
        Cluster.__init__(self)

        if self.action == "create":
            # Set environment
            for i in xrange(0, len(self.replication_controller_dictionary["spec"]["template"]["spec"]["containers"])):
                for j in xrange(0, len(self.replication_controller_dictionary["spec"]["template"]["spec"]["containers"][i]["env"])):
                    if self.replication_controller_dictionary["spec"]["template"]["spec"]["containers"][i]["env"][j]["name"] == "NAMESPACE":
                        self.replication_controller_dictionary["spec"]["template"]["spec"]["containers"][i]["env"][j]["value"] = self.namespace

            self.seed_instance_up_keyword_list = ["Listening for thrift clients"]
            self.all_instance_up_keyword_list = ["Handshaking version with", "is now part of the cluster", "Listening for thrift clients"]
            self.all_instance_failure_keyword_list = ["Exception encountered during startup", "Announcing shutdown"]
        elif self.action == "resize":
            # Set environment
            for i in xrange(0, len(self.replication_controller_dictionary["spec"]["template"]["spec"]["containers"])):
                for j in xrange(0, len(self.replication_controller_dictionary["spec"]["template"]["spec"]["containers"][i]["env"])):
                    if self.replication_controller_dictionary["spec"]["template"]["spec"]["containers"][i]["env"][j]["name"] == "NAMESPACE":
                        self.replication_controller_dictionary["spec"]["template"]["spec"]["containers"][i]["env"][j]["value"] = self.namespace

            self.seed_instance_up_keyword_list = ["Listening for thrift clients"]
            self.all_instance_up_keyword_list = ["Handshaking version with", "is now part of the cluster", "Listening for thrift clients"]
            self.all_instance_failure_keyword_list = ["Exception encountered during startup", "Announcing shutdown"]
        elif self.action == "delete":
            pass



cassandra = Cassandra()
if cassandra.action == "create":
    status_code = cassandra.create_cluster()
    if status_code != Cluster.SUCEESS:
        cassandra.clean_cluster()
        sys.exit(status_code)
elif cassandra.action == "resize":
    status_code = cassandra.resize_cluster(cassandra.size)
    sys.exit(status_code)
elif cassandra.action == "delete":
    status_code = cassandra.clean_cluster()
    sys.exit(status_code)
else:
    print "No such action"
    sys.exit(Cluster.ERROR_NO_SUCH_ACTION_SUPPORT)
