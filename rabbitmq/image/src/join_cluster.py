import httplib2
import json
import yaml
import os
import socket
import random
import time
import traceback


class Cluster:
    def __init__(self):
        self.uri = "https://kubernetes.default.svc.cluster.local:443"
        self.token_file_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
        self.ca_cert_file_path = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
        self.__token = self.__get_token()
        self.hostname = socket.gethostname()
        self.ip = socket.gethostbyname(self.hostname)
        self.namespace = os.environ.get('NAMESPACE', "default")
        self.service = os.environ.get('SERVICE_NAME', "cluster")

    def __get_token(self):
        token_content = ""
        try:
            with open(self.token_file_path, "r") as file_input:
                token_content = file_input.read()
        except Exception as e:
            print e
            traceback.print_exc()
        return "Bearer " + token_content

    def __request(self, method, uri, body, header_dictionary):
        try:
            h = httplib2.Http(ca_certs=self.ca_cert_file_path)
            header, body = h.request(uri, method, body, header_dictionary)

            if header.status == 200:
                return json.loads(body)
            else:
                #print header
                #print body
                return None
        except Exception as e:
            print e
            traceback.print_exc()
            return None

    def get_endpoint(self):
        header_dictionary = {
            "Authorization": self.__token
        }
        result_dictionary = self.__request("GET", self.uri + "/api/v1/namespaces/" + self.namespace + "/endpoints/" + self.service, None, header_dictionary)
        if result_dictionary is None:
            print "Fail to get end point " + self.service
            return None
        else:
            return result_dictionary

    def get_instance_ip_list_without_self(self):
        endpoint_dictionary = self.get_endpoint()
        if endpoint_dictionary is None:
            #print "Fail to get endpoint dictionary"
            return None
        else:
            instance_ip_list = []
            if endpoint_dictionary.get("subsets") != None:
                for subset_dictionary in endpoint_dictionary["subsets"]:
                    for address_dictionary in subset_dictionary["addresses"]:
                        # Don't include self
                        if address_dictionary["targetRef"]["name"] != self.hostname:
                            instance_ip_list.append(address_dictionary["ip"])

            return instance_ip_list
            
    def delete_pod(self):
        header_dictionary = {
            "Authorization": self.__token
        }
        # Hostname is the pod name
        result_dictionary = self.__request("DELETE", self.uri + "/api/v1/namespaces/" + self.namespace + "/pods/" + self.hostname, None, header_dictionary)
        if result_dictionary is None:
            print "Fail to delete pod " + self.hostname
            return None
        else:
            print "Pod " + self.hostname + " is deleted"
            return result_dictionary

    def get_instance_ip_list_without_self_retry(self):
        for i in xrange(0, self.get_instance_ip_list_retry_amount):
            instance_ip_list = self.get_instance_ip_list_without_self()
            if instance_ip_list is not None and len(instance_ip_list) > 0:
                break
            else:
                # Randomly sleep to prevent all instances run at the same time
                random_sleep_in_second = random.randint(1, 10)
                time.sleep(random_sleep_in_second)
        if instance_ip_list is None:
            instance_ip_list = []
        return instance_ip_list
            
    def join_cluster(self):
        self.instance_ip_list = self.get_instance_ip_list_without_self_retry()

        if self.instance_ip_list is None or len(self.instance_ip_list) == 0:
            self.seed_instance_action_before_running()
            result = os.system(self.star_script)
            if result == 0:
                self.seed_instance_action_after_running()
                print "Seed instance started"
                return True
            else:
                print "Fail to start seed instance"
                return False
        else:
            self.joining_instance_action_before_running()
            result = os.system(self.star_script)
            if result == 0:
                self.joining_instance_action_after_running()
                print "Instance joined cluster"
                return True
            else:
                print "Fail to join cluster"
                #self.delete_pod()
                return False
            
            
class RabbitMQCluter(Cluster):
    def __init__(self):
        Cluster.__init__(self)
    
        self.star_script = ""
        self.get_instance_ip_list_retry_amount = 3
        self.cluster_name = self.namespace + "_" + self.service

    def __add_hosts_and_get_instance_name_list(self):
        endpoint_dictionary = self.get_endpoint()
        if endpoint_dictionary is None:
            print "Fail to get endpoint dictionary so this instance is used as seed"
            return None
        else:
            hostname_and_ip_list = []
            instance_name_list = []
            for subset_dictionary in endpoint_dictionary["subsets"]:
                for address_dictionary in subset_dictionary["addresses"]:
                    hostname_and_ip_list.append(address_dictionary["ip"] + " " + address_dictionary["targetRef"]["name"] + "\n")
                    instance_name_list.append(address_dictionary["targetRef"]["name"])

            with open("/etc/hosts", "a") as file_append:
                for hostname_and_ip in hostname_and_ip_list:
                    file_append.write(hostname_and_ip)

            return instance_name_list

    def __configure(self):
        instance_name_list = self.__add_hosts_and_get_instance_name_list()
        if instance_name_list is None:
            return True
        else:
            for instance_name in instance_name_list:
                # Join only other instances
                if instance_name != self.hostname:
                    result = os.system("rabbitmqctl stop_app")
                    if result == 0:
                        result = os.system("rabbitmqctl join_cluster rabbit@" + instance_name)
                        if result == 0:
                            result = os.system("rabbitmqctl start_app")
                            if result == 0:
                                print "Instance joined cluster"
                                return True

            print "Fail to join cluster"
            return False

    def seed_instance_action_before_running(self):
        self.__configure()
        
    def seed_instance_action_after_running(self):
        pass
    
    def joining_instance_action_before_running(self):
        self.__configure()
        
    def joining_instance_action_after_running(self):
        pass


RabbitMQCluter().join_cluster()
