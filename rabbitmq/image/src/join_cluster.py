import httplib2
import json
import os
import socket


class KubernetesService:
    def __init__(self):
        self.uri = "https://kubernetes.default.svc.cluster.local:443"
        self.token_file_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
        self.ca_cert_file_path = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
        self.__token = self.__get_token()
        self.hostname = socket.gethostname()
        self.namespace = os.environ.get('NAMESPACE', "default")
        self.service = os.environ.get('SERVICE_NAME', "")
        

    def __get_token(self):
        token_content = ""
        with open(self.token_file_path, "r") as file_input:
            token_content = file_input.read()
        return "Bearer " + token_content

    def __request(self, method, uri, body, header_dictionary):
        h = httplib2.Http(ca_certs=self.ca_cert_file_path)
        header, body = h.request(uri, method, body, header_dictionary)

        if header.status == 200:
            return json.loads(body)
        else:
            print header
            print body
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


class RabbitMQCluter:
    def __init__(self):
        self.kubernetes_service = KubernetesService()

    def __add_hosts_and_get_instance_name_list(self):
        endpoint_dictionary = self.kubernetes_service.get_endpoint()
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

    def join_cluster(self):
        instance_name_list = self.__add_hosts_and_get_instance_name_list()
        if instance_name_list is None:
            print "Seed instance started"
            return True
        else:
            for instance_name in instance_name_list:
                # Join only other instances
                if instance_name != self.kubernetes_service.hostname:
                    result = os.system("rabbitmqctl stop_app")
                    if result == 0:
                        result = os.system("rabbitmqctl join_cluster rabbit@" + instance_name)
                        if result == 0:
                            result = os.system("rabbitmqctl start_app")
                            if result == 0:
                                print "Instance joined cluster"
                                return True

            print "Fail to join cluster"
            self.kubernetes_service.delete_pod()
            return False


RabbitMQCluter().join_cluster()
