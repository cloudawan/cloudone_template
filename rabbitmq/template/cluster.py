__author__ = 'ycchang'


import sys
import json
import os
import time
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
    def __init__(self):
        self.parameter_dictionary = {
            "application_name": None,
            "kubeapi_host_and_port": None,
            "namespace": None,
            "size": None,
            "service_file_name": None,
            "replication_controller_file_name": None,
            "timeout_in_second": None,
            "action": None,
        }

        if self.__handle_input() is False:
            sys.exit(-1)
        else:
            print "Parameters are: " + str(self.parameter_dictionary)
    
        self.http = Http()

        self.application_name = self.parameter_dictionary.get("application_name", "name")#name
        self.kubeapi_host_and_port = self.parameter_dictionary.get("kubeapi_host_and_port", "http://127.0.0.1:8080")#"http://127.0.0.1:8080
        self.size = int(self.parameter_dictionary.get("size", 1))#3
        self.service_file_name = self.parameter_dictionary.get("service_file_name", "service.json")#"service.json"
        self.replication_controller_file_name = self.parameter_dictionary.get("replication_controller_file_name", "replication-controller.json")#"replication-controller.json"
        self.time_to_wait = int(self.parameter_dictionary.get("timeout_in_second", 60))#60 * 3
        self.namespace = self.parameter_dictionary.get("namespace", "default")#default
        self.action = self.parameter_dictionary.get("action", "create")#create

        self.replication_controller_dictionary = self.__load_replication_controller_file()
        self.service_dictionary = self.__load_service_file()
   
        self.service_name = self.application_name#self.service_dictionary.get("metadata").get("name")
        self.replication_controller_name = self.application_name#self.replication_controller_dictionary.get("metadata").get("name")
        self.pod_keyword_prefix = self.replication_controller_dictionary.get("metadata").get("name")

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

    def __load_replication_controller_file(self):
        with open(self.replication_controller_file_name, "r") as file_read:
            text = file_read.read()
            return json.loads(text)

    def __load_service_file(self):
        with open(self.service_file_name, "r") as file_read:
            text = file_read.read()
            return json.loads(text)

    # Check seed node
    def __check_seed_node_up(self, pod_list):
        for pod in pod_list:
            head, body = self.http.request(
                self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace + "/pods/" + pod + "/log", "GET")
            for seed_node_up_keyword in self.seed_node_up_keyword_list:
                if seed_node_up_keyword in body:
                    pass
                else:
                    return None
        return True

    # Check all nodes are up in the cluster
    def __check_all_node_up(self, pod_list):
        for pod in pod_list:
            head, body = self.http.request(
                self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace + "/pods/" + pod + "/log", "GET")
            for all_node_up_keyword in self.all_node_up_keyword_list:
                if all_node_up_keyword in body:
                    pass
                else:
                    return None
            for all_node_failure_keyword in self.all_node_failure_keyword_list:
                if all_node_failure_keyword in body:
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

    # Get all node name
    def __get_all_pod_name(self, expected_size=-1):
        pod_list = []
        head, body = self.http.request(
            self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace + "/pods/", "GET")
        dictionary = json.loads(body)
        for item in dictionary.get("items"):
            if item.get("metadata").get("name").startswith(self.pod_keyword_prefix):
                pod_list.append(item.get("metadata").get("name"))

        if expected_size == -1 or expected_size == len(pod_list):
            return pod_list
        else:
            return None

    def create_cluster(self):
        # Create a replication controller
        self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace +
                          "/replicationcontrollers", "POST", json.dumps(self.replication_controller_dictionary))

        # Get seed pod name
        seed_pod_list = Utility.execute_until_timeout(self.__get_all_pod_name, self.time_to_wait, 1)
        if seed_pod_list is False:
            print("Fail to get seed pod name")
            return False
        else:
            print("The created seed pod is:  " + str(seed_pod_list))

        # Check seed pod
        if Utility.execute_until_timeout(self.__check_seed_node_up, self.time_to_wait, seed_pod_list):
            print("Successfully create the seed node")
        else:
            print("Seed node fail to come up")
            return False

        # Create a service to track all nodes
        self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace +
                          "/services", "POST", json.dumps(self.service_dictionary))
            
        # Check service
        if Utility.execute_until_timeout(self.__check_service_up, self.time_to_wait):
            print("Successfully create the service")
        else:
            print("Service fail to come up")
            return False
            
        # Resize
        if self.size > 1:
            for i in xrange(1, self.size):
                if self.resize_cluster(i + 1) is False:
                    return False
            return True
        else:
            return True

    def clean_cluster(self):
        self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace + "/services/" +
                          self.service_name, "DELETE")
        self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace + "/replicationcontrollers/" +
                          self.replication_controller_name, "DELETE")

        pod_list = self.__get_all_pod_name()
        for pod in pod_list:
            self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace + "/pods/" +
                              pod, "DELETE")
                              
    def resize_cluster(self, size):
        # Get seed pod name
        seed_pod_list = Utility.execute_until_timeout(self.__get_all_pod_name, self.time_to_wait, size-1)
        if seed_pod_list is False:
            print("Fail to get seed pod name")
            return False
        else:
            print("The created seed pod is:  " + str(seed_pod_list))
            
        # Resize
        head, body = self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace +
                                       "/replicationcontrollers/" + self.replication_controller_name, "GET")
        if head.status != 200:
            print "Fail to get the current replication controller data"
            print head
            print body
            return False

        replication_controller_dictionary = json.loads(body)
        replication_controller_dictionary["spec"]["replicas"] = size

        head, body = self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace +
                                       "/replicationcontrollers/" + self.replication_controller_name, "PUT",
                                       json.dumps(replication_controller_dictionary))
        if head.status != 200:
            print "Fail to put the new replication controller data"
            print head
            print body
            return False

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
        # Check for all nodes
        if Utility.execute_until_timeout(self.__check_all_node_up, self.time_to_wait, pod_without_seed_list):
            print("Successfully resize the cluster")
            return True
        else:
            print("One or more nodes fail to join the cluster")
            return False


class Rabbitmq(Cluster):
    def __init__(self):
        Cluster.__init__(self)
        
        # Set environment
        for i in xrange(0, len(self.replication_controller_dictionary["spec"]["template"]["spec"]["containers"])):
            for j in xrange(0, len(self.replication_controller_dictionary["spec"]["template"]["spec"]["containers"][i]["env"])):
                if self.replication_controller_dictionary["spec"]["template"]["spec"]["containers"][i]["env"][j]["name"] == "NAMESPACE":
                    self.replication_controller_dictionary["spec"]["template"]["spec"]["containers"][i]["env"][j]["value"] = self.namespace
    
        self.seed_node_up_keyword_list = ["Seed instance started"]
        self.all_node_up_keyword_list = ["Instance joined cluster"]
        self.all_node_failure_keyword_list = ["Fail to join cluster"]


rabbitmq = Rabbitmq()
if rabbitmq.action == "create":
    if not rabbitmq.create_cluster():
        rabbitmq.clean_cluster()
        sys.exit(-1)
elif rabbitmq.action == "clean":
    rabbitmq.clean_cluster()
elif rabbitmq.action == "resize":
    rabbitmq.resize_cluster()
else:
    print "No such action"