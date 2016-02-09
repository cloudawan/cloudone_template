from cassandra.cluster import Cluster
from config import cluster_location

cluster = Cluster(cluster_location, port=9042)



session = cluster.connect()
session.execute("CREATE KEYSPACE keyspace_test WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 5 };")
session.set_keyspace('keyspace_test')
session.execute("CREATE TABLE users (id int PRIMARY KEY, address text)")



