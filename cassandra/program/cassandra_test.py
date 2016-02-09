from cassandra.cluster import Cluster

cluster = Cluster(['4.0.89.2', '4.0.9.2', '4.0.91.2'], port=9042)


session = cluster.connect()
#session.execute("CREATE KEYSPACE keyspace_test WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 5 };")
session.set_keyspace('keyspace_test')
session.execute("CREATE TABLE users (id int PRIMARY KEY, address text)")

# insert a row using an instance of Address
session.execute("INSERT INTO users (id, address) VALUES (%s, %s)", (0, "123 Main St."))

# results will include Address instances
results = session.execute("SELECT * FROM users")
row = results[0]
print row.id, row.address


