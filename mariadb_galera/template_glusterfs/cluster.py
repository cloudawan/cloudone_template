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


class ClusterWithGlusterfs:
    SUCEESS = 0
    ERROR_OTHER = 1
    ERROR_NO_SUCH_ACTION_SUPPORT = 2
    ERROR_NO_ACTION_PARAMETER = 3
    ERROR_PARAMETER_MISSING = 4
    ERROR_SIZE_LESS_THAN_ONE = 5
    ERROR_SIZE_DIFFERENT_FROM_GLUSTERFS_PATH_AMOUNT = 6
    ERROR_FAIL_TO_CREATE_SEED_INSTANCE = 7
    ERROR_FAIL_TO_CREATE_SERVICE = 8
    ERROR_FAIL_TO_CREATE_JOINING_INSTANCE = 9
    ERROR_FAIL_TO_GET_OWNING_REPLICATION_CONTROLLER_LIST = 10
    ERROR_FAIL_TO_DELETE_SERVICE = 11
    ERROR_FAIL_TO_DELETE_REPLICATION_CONTROLLER = 12
    ERROR_FAIL_TO_DELETE_POD = 13

    def __init__(self):
        self.parameter_dictionary = self.__get_input()
        self.action = self.parameter_dictionary.get("action")
        if self.action == None:
            sys.exit(ClusterWithGlusterfs.ERROR_NO_ACTION_PARAMETER)

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
                sys.exit(ClusterWithGlusterfs.ERROR_PARAMETER_MISSING)
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
                sys.exit(ClusterWithGlusterfs.ERROR_PARAMETER_MISSING)
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
                sys.exit(ClusterWithGlusterfs.ERROR_PARAMETER_MISSING)
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
        self.environment_pair_list = self.__load_environment_file()
        # Indirect Data
        self.service_name = self.application_name #self.service_dictionary.get("metadata").get("name")
        self.replication_controller_name = self.application_name + "-instance" #self.replication_controller_dictionary.get("metadata").get("name")
        self.glusterfs_path_list = self.__get_glusterfs_path_list()
        self.glusterfs_endpoints = self.__get_glusterfs_endpoints()

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
        self.environment_pair_list = self.__load_environment_file()
        # Indirect Data
        self.service_name = self.application_name #self.service_dictionary.get("metadata").get("name")
        self.replication_controller_name = self.application_name + "-instance" #self.replication_controller_dictionary.get("metadata").get("name")
        self.glusterfs_path_list = self.__get_glusterfs_path_list()
        self.glusterfs_endpoints = self.__get_glusterfs_endpoints()

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
        
    def __get_glusterfs_path_list(self):
        for environment_pair in self.environment_pair_list:
            if environment_pair.get("name") == "GLUSTERFS_PATH_LIST":
                glusterfs_path_list = environment_pair.get("value").split(",")
                for i in xrange(0, len(glusterfs_path_list)):
                    glusterfs_path_list[i] = glusterfs_path_list[i].strip()
                return glusterfs_path_list
        return []
        
    def __get_glusterfs_endpoints(self):
        for environment_pair in self.environment_pair_list:
            if environment_pair.get("name") == "GLUSTERFS_ENDPOINTS":
                return environment_pair.get("value")
        return None
        
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

    def __load_environment_file(self):
        with open(self.environment_file_name, "r") as file_read:
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

    # Check joining nodes are up in the cluster
    def __check_joining_instance_up(self, pod_list):
        for pod in pod_list:
            head, body = self.http.request(
                self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace + "/pods/" + pod + "/log", "GET")
            for joining_instance_up_keyword in self.joining_instance_up_keyword_list:
                if joining_instance_up_keyword in body:
                    pass
                else:
                    return None
            for joining_node_failure_keyword in self.joining_node_failure_keyword_list:
                if joining_node_failure_keyword in body:
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

    # Get all pod name
    def __get_all_pod_name_in_replication_controller(self, expected_size, replication_controller_number):
        pod_list = []
        head, body = self.http.request(
            self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace + "/pods/", "GET")
        dictionary = json.loads(body)
        for item in dictionary.get("items"):
            # Remove the pod name part -xxxxx
            name = item.get("metadata").get("name")[:-6]
            if name == self.__get_replication_controller_instance_name(replication_controller_number):
                pod_list.append(item.get("metadata").get("name"))

        if expected_size == -1 or expected_size == len(pod_list):
            return pod_list
        else:
            return None
            
    def __get_replication_controller_instance_name(self, replication_controller_number):
        return self.replication_controller_name + "-" + str(replication_controller_number)

    def __create_replication_controller(self, replication_controller_number):
        replication_controller_dictionary = copy.deepcopy(self.replication_controller_dictionary)
        replication_controller_dictionary["metadata"]["name"] = self.__get_replication_controller_instance_name(replication_controller_number)
        replication_controller_dictionary["metadata"]["labels"]["name"] = self.__get_replication_controller_instance_name(replication_controller_number)
        replication_controller_dictionary["spec"]["selector"]["name"] = self.__get_replication_controller_instance_name(replication_controller_number)
        replication_controller_dictionary["spec"]["template"]["metadata"]["labels"]["name"] = self.__get_replication_controller_instance_name(replication_controller_number)
        
        replication_controller_dictionary["spec"]["selector"]["group"] = self.service_name
        replication_controller_dictionary["spec"]["template"]["metadata"]["labels"]["group"] = self.service_name
        
        volume_list = replication_controller_dictionary["spec"]["template"]["spec"]["volumes"]
        for volume in volume_list:
            if volume.get("name") == self.volume_to_mount:
                volume["glusterfs"]["endpoints"] = self.glusterfs_endpoints
                volume["glusterfs"]["path"] = self.glusterfs_path_list[replication_controller_number]
                
        return replication_controller_dictionary
    
    def __create_service(self):
        service_dictionary = copy.deepcopy(self.service_dictionary)
        service_dictionary["metadata"]["name"] = self.service_name
        service_dictionary["metadata"]["labels"]["name"] = self.service_name
        service_dictionary["spec"]["selector"]["group"] = self.service_name
        
        return service_dictionary
    
    def __create_replication_controller_and_check(self, replication_controller_number, check_function):
        # Create a replication controller
        self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace +
                          "/replicationcontrollers", "POST", json.dumps(self.__create_replication_controller(replication_controller_number)))

        # Get pod name
        pod_list = Utility.execute_until_timeout(self.__get_all_pod_name_in_replication_controller, self.time_to_wait, 1, replication_controller_number)
        if pod_list is False:
            print("Fail to get pod name for replication controller number " + str(replication_controller_number))
            return False
        else:
            print("The created pod for replication controller number " + str(replication_controller_number) + " is:  " + str(pod_list))

        # Check pod
        if Utility.execute_until_timeout(check_function, self.time_to_wait, pod_list):
            print("Successfully create the instance")
        else:
            print("Instance fail to come up")
            return False
    
    def __get_owning_replication_controller_list(self):
        head, body = self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace +
                                       "/replicationcontrollers", "GET")
        if head.status == 200:
            owning_replication_controller_list = []
            dictionary = json.loads(body)
            item_list = dictionary.get("items")
            for item in item_list:
                selector_group = item.get("spec").get("selector").get("group") 
                selector_name = item.get("spec").get("selector").get("name") 
                if selector_group == self.service_name and selector_name.startswith(self.replication_controller_name):
                    owning_replication_controller_list.append(item.get("metadata").get("name"))
            return owning_replication_controller_list, ClusterWithGlusterfs.SUCEESS
        else:
            print "Fail to get owning replication controller list"
            print head
            print body
            return None, ClusterWithGlusterfs.ERROR_FAIL_TO_GET_OWNING_REPLICATION_CONTROLLER_LIST
    
    def create_cluster(self):
        # Check
        if self.size < 1:
            print("Size " + str(self.size) + " can't be less than 1")
            return ClusterWithGlusterfs.ERROR_SIZE_LESS_THAN_ONE
        if len(self.glusterfs_path_list) != self.size:
            print("Size " + str(self.size) + " is not the same as the path list " + str(self.glusterfs_path_list) + " amount " + str(len(self.glusterfs_path_list)))
            return ClusterWithGlusterfs.ERROR_SIZE_DIFFERENT_FROM_GLUSTERFS_PATH_AMOUNT
    
        # Create and check seed instance
        if self.__create_replication_controller_and_check(0, self.__check_seed_instance_up) is False:
            print("Fail to create seed instance")
            return ClusterWithGlusterfs.ERROR_FAIL_TO_CREATE_SEED_INSTANCE
    
        # Create a service to track joining instances
        self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace +
                          "/services", "POST", json.dumps(self.__create_service()))
            
        # Check service
        if Utility.execute_until_timeout(self.__check_service_up, self.time_to_wait):
            print("Successfully create the service")
        else:
            print("Fail to create service")
            return ClusterWithGlusterfs.ERROR_FAIL_TO_CREATE_SERVICE
            
        # Add other instances
        if self.size > 1:
            for i in xrange(1, self.size):
                if self.__create_replication_controller_and_check(i, self.__check_joining_instance_up) is False:
                    print("Fail to create joining instance " + str(i))
                    return ClusterWithGlusterfs.ERROR_FAIL_TO_CREATE_JOINING_INSTANCE
            return ClusterWithGlusterfs.SUCEESS
        else:
            return ClusterWithGlusterfs.SUCEESS

    def resize_cluster(self):
        owning_replication_controller_list, status_code = self.__get_owning_replication_controller_list()
        if status_code != ClusterWithGlusterfs.SUCEESS:
            return status_code
            
        current_size = len(owning_replication_controller_list)
        
        if self.size == current_size:
            print "Size is not changed"
            return ClusterWithGlusterfs.SUCEESS
        elif self.size < current_size:
            # Delete replication controllers and related pods
            for i in xrange(self.size, current_size):
                head, body = self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace + "/replicationcontrollers/" + 
                                               self.__get_replication_controller_instance_name(i), "DELETE")
                if head.status != 200:
                    print "Fail to delete replication controller " + self.__get_replication_controller_instance_name(i)
                    print head
                    print body
                    return ClusterWithGlusterfs.ERROR_FAIL_TO_DELETE_REPLICATION_CONTROLLER
                                  
                pod_list = Utility.execute_until_timeout(self.__get_all_pod_name_in_replication_controller, self.time_to_wait, -1, i)

                for pod in pod_list:
                    head, body = self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace + "/pods/" + pod, "DELETE")
                    if head.status != 200:
                        print "Fail to delete pod " + pod
                        print head
                        print body
                        return ClusterWithGlusterfs.ERROR_FAIL_TO_DELETE_POD

            return ClusterWithGlusterfs.SUCEESS
        elif self.size > current_size:
            # Create replication controllers
            for i in xrange(current_size, self.size):
                if self.__create_replication_controller_and_check(i, self.__check_joining_instance_up) is False:
                    print("Fail to create joining instance " + str(i))
                    return ClusterWithGlusterfs.ERROR_FAIL_TO_CREATE_JOINING_INSTANCE
            return ClusterWithGlusterfs.SUCEESS
            
    def clean_cluster(self):
        owning_replication_controller_list, status_code = self.__get_owning_replication_controller_list()
        if status_code != ClusterWithGlusterfs.SUCEESS:
            return status_code
    
        size = len(owning_replication_controller_list)
    
        head, body = self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace + "/services/" + self.service_name, "DELETE")
        if head.status != 200:
            print "Fail to delete service " + self.service_name
            print head
            print body
            return ClusterWithGlusterfs.ERROR_FAIL_TO_DELETE_SERVICE
        
        for i in xrange(0, size):
            head, body = self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace + "/replicationcontrollers/" + 
                                           self.__get_replication_controller_instance_name(i), "DELETE")
            if head.status != 200:
                print "Fail to delete replication controller " + self.__get_replication_controller_instance_name(i)
                print head
                print body
                return ClusterWithGlusterfs.ERROR_FAIL_TO_DELETE_REPLICATION_CONTROLLER
                              
            pod_list = Utility.execute_until_timeout(self.__get_all_pod_name_in_replication_controller, self.time_to_wait, -1, i)

            for pod in pod_list:
                head, body = self.http.request(self.kubeapi_host_and_port + "/api/v1/namespaces/" + self.namespace + "/pods/" + pod, "DELETE")
                if head.status != 200:
                    print "Fail to delete pod " + pod
                    print head
                    print body
                    return ClusterWithGlusterfs.ERROR_FAIL_TO_DELETE_POD
        
        return ClusterWithGlusterfs.SUCEESS


class Mariadb(ClusterWithGlusterfs):
    def __init__(self):
        ClusterWithGlusterfs.__init__(self)
        
        if self.action == "create":
            # Set environment
            for i in xrange(0, len(self.replication_controller_dictionary["spec"]["template"]["spec"]["containers"])):
                for j in xrange(0, len(self.replication_controller_dictionary["spec"]["template"]["spec"]["containers"][i]["env"])):
                    if self.replication_controller_dictionary["spec"]["template"]["spec"]["containers"][i]["env"][j]["name"] == "NAMESPACE":
                        self.replication_controller_dictionary["spec"]["template"]["spec"]["containers"][i]["env"][j]["value"] = self.namespace

            self.volume_to_mount = "mariadb-galera-volume"
            self.seed_instance_up_keyword_list = ["Seed instance started"]
            self.joining_instance_up_keyword_list = ["Instance joined cluster"]
            self.joining_node_failure_keyword_list = ["Fail to join cluster"]
        elif self.action == "resize":
            # Set environment
            for i in xrange(0, len(self.replication_controller_dictionary["spec"]["template"]["spec"]["containers"])):
                for j in xrange(0, len(self.replication_controller_dictionary["spec"]["template"]["spec"]["containers"][i]["env"])):
                    if self.replication_controller_dictionary["spec"]["template"]["spec"]["containers"][i]["env"][j]["name"] == "NAMESPACE":
                        self.replication_controller_dictionary["spec"]["template"]["spec"]["containers"][i]["env"][j]["value"] = self.namespace

            self.volume_to_mount = "mariadb-galera-volume"
            self.seed_instance_up_keyword_list = ["Seed instance started"]
            self.joining_instance_up_keyword_list = ["Instance joined cluster"]
            self.joining_node_failure_keyword_list = ["Fail to join cluster"]
        elif self.action == "delete":
            pass


mariadb = Mariadb()
if mariadb.action == "create":
    status_code = mariadb.create_cluster()
    if status_code != ClusterWithGlusterfs.SUCEESS:
        mariadb.clean_cluster()
        sys.exit(status_code)
elif mariadb.action == "resize":
    status_code = mariadb.resize_cluster()
    sys.exit(status_code)
elif mariadb.action == "delete":
    status_code = mariadb.clean_cluster()
    sys.exit(status_code)
else:
    print "No such action"
    sys.exit(ClusterWithGlusterfs.ERROR_NO_SUCH_ACTION_SUPPORT)