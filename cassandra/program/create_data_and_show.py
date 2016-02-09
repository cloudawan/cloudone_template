from cassandra.cluster import Cluster
from config import cluster_location

cluster = Cluster(cluster_location, port=9042)

session = cluster.connect()
session.execute("USE keyspace_test")

# insert a row using an instance of Address
session.execute("INSERT INTO users (id, address) VALUES (%s, %s)", (0, "123 Main St."))
session.execute("INSERT INTO users (id, address) VALUES (%s, %s)", (1, "456 North St."))
session.execute("INSERT INTO users (id, address) VALUES (%s, %s)", (2, "789 South St."))

# results will include Address instances
results = session.execute("SELECT * FROM users")

for row in results:
 print row.id, row.address


