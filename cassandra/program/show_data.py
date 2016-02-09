from cassandra.cluster import Cluster
from config import cluster_location

cluster = Cluster(cluster_location, port=9042)
session = cluster.connect()
session.execute("USE keyspace_test")

# results will include Address instances
results = session.execute("SELECT * FROM users")

for row in results:
 print row.id, row.address


