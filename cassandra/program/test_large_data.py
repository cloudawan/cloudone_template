import uuid
import sys
from time import time
# sudo apt-get install python-dev
# pip install cassandra-driver
from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster


class Cassandra:
	def __init__(self):
		self.__cluster_host = ["192.168.0.31","192.168.0.32","192.168.0.33"]
		self.__port=32095
		self.__keyspace = "keyspace_test"
		self.__strategy = "CREATE KEYSPACE IF NOT EXISTS " + self.__keyspace + " WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 3 };"
		self.__table = "test_data"
		self.__table_schema = "CREATE TABLE IF NOT EXISTS " + self.__table + " (id int PRIMARY KEY, in_boolean boolean, in_int int, in_bigint bigint, in_float float, in_varchar varchar, in_text text, in_uuid uuid, in_blob blob)"
		self.__cluster = Cluster(self.__cluster_host, port=self.__port)
		self.__session = self.__cluster.connect()
		self.__session.default_consistency_level = ConsistencyLevel.LOCAL_QUORUM
		self.__amount_to_show_progress = 1000
	
	def __start_timer(self):
		self.previous_time=time()
		
	def __current_timer(self):
		return time()-self.previous_time
		
	def __end_timer(self):
		self.now_time=time()
		print "Use time(s):" + str(self.now_time-self.previous_time)
	
	def create_keyspace(self):
		self.__session.execute(self.__strategy)

	def create_table(self):
		self.__session.set_keyspace(self.__keyspace)
		self.__session.execute(self.__table_schema)

	def __create_data(self, i):
		if i % 2 == 0:
			in_boolean=False
		else:
			in_boolean=True
		in_int=i
		in_bigint=long(i)
		in_float=float(i)
		in_varchar=str(i)
		in_text=unicode(i)
		in_uuid=uuid.UUID(int=i)
		in_blob=bytearray(str(i))
		return i, in_boolean, in_int, in_bigint, in_float, in_varchar, in_text, in_uuid, in_blob
		
	def insert_data(self, start, end):
		self.__start_timer()
		self.__session.set_keyspace(self.__keyspace)
		amount=end-start
		insert_amount = 0
		for i in xrange(start, end):
			try:
				if i % self.__amount_to_show_progress == 0:
					print "Use time(s):" + str(self.__current_timer()) + "   " + str(i) + " - (" + str(start) + "~" + str(end) + ")" + " processed_amount/total_amount " + str(insert_amount) + "/" + str(amount)
				#before_execute_time=self.__current_timer()
				# %s should be used for all types of data according to the document of Cassandra python client
				self.__session.execute("INSERT INTO " + self.__table + " (id, in_boolean, in_int, in_bigint, in_float, in_varchar, in_text, in_uuid, in_blob) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", self.__create_data(i))
				insert_amount+=1
			except Exception as e:
				print e
				#print "Use time(s):" + str(before_execute_time) + " before Exception"
				print "Use time(s):" + str(self.__current_timer()) + " Exception"
		self.__end_timer()
	
	def delete_all(self):
		self.__start_timer()
		self.__session.set_keyspace(self.__keyspace)
		self.__session.execute("TRUNCATE " + self.__table)
		self.__end_timer()
	
	def verify_data(self, id):
		self.__session.set_keyspace(self.__keyspace)
		row_list = self.__session.execute("SELECT * FROM " + self.__table + " WHERE id=" + str(id))
		for row in row_list:
			i, in_boolean, in_int, in_bigint, in_float, in_varchar, in_text, in_uuid, in_blob = self.__create_data(id)
			if i == row.id and in_boolean == row.in_boolean and in_int == row.in_int and in_bigint == row.in_bigint and in_float == row.in_float and in_varchar == row.in_varchar and in_text == row.in_text and in_uuid == row.in_uuid and in_blob == row.in_blob:
				return True
			else:
				return False
				
	def verify_all(self, start, end):
		self.__start_timer()
		amount=end-start
		valid_amount = 0
		for i in xrange(start, end):
			if i % self.__amount_to_show_progress == 0:
				print "Use time(s):" + str(self.__current_timer()) + "   " + str(i) + " - (" + str(start) + "~" + str(end) + ")" + " processed_amount/total_amount " + str(valid_amount) + "/" + str(amount)
			if self.verify_data(i):
				valid_amount+=1
		print str(valid_amount) + "/" + str(amount)
		self.__end_timer()
	
	def close(self):
		self.__cluster.shutdown()


if len(sys.argv) >= 2:
	action = sys.argv[1]
else:
	action = None
	print "usage: create/insert amount/verify id/verify_all amount/delete_all"

if action == "create":
	cassandra=Cassandra()
	cassandra.create_keyspace()
	cassandra.create_table()
	cassandra.close()
elif action == "insert":
	if len(sys.argv) == 4:
		start = int(sys.argv[2])
		end = int(sys.argv[3])
		cassandra=Cassandra()
		cassandra.create_keyspace()
		cassandra.create_table()
		cassandra.insert_data(start, end)
		cassandra.close()
	else:
		print "usage: insert start end"
elif action == "verify":
	if len(sys.argv) == 3:
		id = int(sys.argv[2])
		cassandra=Cassandra()
		print cassandra.verify_data(id)
		cassandra.close()
	else:
		print "usage: insert id"
elif action == "verify_all":
	if len(sys.argv) == 4:
		start = int(sys.argv[2])
		end = int(sys.argv[3])
		cassandra=Cassandra()
		cassandra.verify_all(start, end)
		cassandra.close()
	else:
		print "usage: verify_all start end"
elif action == "delete_all":
	cassandra=Cassandra()
	cassandra.delete_all()
	cassandra.close()
else:
	print "No valid action"