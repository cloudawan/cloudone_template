# make all node share the same Erlang cookie
cp -f /src/.erlang.cookie  /var/lib/rabbitmq/.erlang.cookie
chown rabbitmq:rabbitmq /var/lib/rabbitmq/.erlang.cookie
chmod 400 /var/lib/rabbitmq/.erlang.cookie

# Run rabbitmq in background
rabbitmq-server -detached
sleep 10
# Create user
rabbitmqctl add_user $USER_USERNAME $USER_PASSWORD
rabbitmqctl set_permissions -p / $USER_USERNAME "$USER_PRIVILEGE_CONFIG" "$USER_PRIVILEGE_WRITE" "$USER_PRIVILEGE_READ"

rabbitmqctl set_policy all '^.' '{"ha-mode":"all"}'

# Join cluster
python /src/join_cluster.py

while :
do
	sleep 1
done
 