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


class MariaDBGaleraCluter(Cluster):
    def __init__(self):
        Cluster.__init__(self)
    
        self.configuration_file_path = "/etc/mysql/conf.d/galera.cnf"
        self.star_script = "service mysql restart"
        self.get_instance_ip_list_retry_amount = 3
        self.cluster_name = self.namespace + "_" + self.service
        self.xtrabackup_password = os.environ.get('XTRABACKUP_PASSWORD', 'password')
        self.root_password = os.environ.get('ROOT_PASSWORD', 'password')

    def __configure(self):
        # Read configuration
        with open(self.configuration_file_path, "r") as file_read:
            line_list = file_read.readlines()

        # Cluster name
        for i in xrange(0, len(line_list)):
            if line_list[i].startswith("wsrep_cluster_address=gcomm://"):
                length = len("wsrep_cluster_address=gcomm://")
                line_list[i] = line_list[i][:length] + ",".join(self.instance_ip_list) + os.linesep

        # Write configuration    
        with open(self.configuration_file_path, "w") as file_write:
            file_write.writelines(line_list)

    def __set_mysql_user_password_privilege(self):
        # Set password and privilege. root need to be in the last since after that, the command requires password.
        os.system("mysql -e \"FLUSH PRIVILEGES;CREATE USER 'xtrabackup'@'localhost' IDENTIFIED BY '" + self.xtrabackup_password + "';GRANT RELOAD,LOCK TABLES,REPLICATION CLIENT ON *.* TO 'xtrabackup'@'localhost';FLUSH PRIVILEGES;\"")
        os.system("mysql -e \"DELETE FROM mysql.user WHERE user='root';FLUSH PRIVILEGES;CREATE USER 'root'@'%' IDENTIFIED BY '" + self.root_password + "';GRANT ALL ON *.* TO 'root'@'%' WITH GRANT OPTION;FLUSH PRIVILEGES;\"")

    def seed_instance_action_before_running(self):
        pass
        
    def seed_instance_action_after_running(self):
        self.__set_mysql_user_password_privilege()
    
    def joining_instance_action_before_running(self):
        self.__configure()
        
    def joining_instance_action_after_running(self):
        pass


MariaDBGaleraCluter().join_cluster()
