#!/bin/sh

#if [ -z "$XTRABACKUP_PASSWORD" ]; then
#	echo "XTRABACKUP_PASSWORD not set"
#	exit 1
#fi

#if [ -z "$ROOT_PASSWORD" ]; then
#	echo "ROOT_PASSWORD not set"
#	exit 2
#fi

mount_path=/var/lib/mysql
data_path=$mount_path/data

# Recover or initialize the empty container

# Check for mysql.* schema
# If it does not exists we got to create it
test -d $data_path/mysql
if [ $? != 0 ]; then
	mysql_install_db --user=mysql
	if [ $? != 0 ]; then
		echo "Fail to install mysql.* schema because $data_path is empty"
	fi
fi

# Get the GTID possition
echo  "Get the GTID positon"
tmpfile=$(mktemp)
mysqld --wsrep-recover 2>${tmpfile}
if [ $? != 0 ]; then
	echo "Error to start with --wsrep-recover"
	cat ${tmpfile}
	exit 3
fi

wsrep_start_position=$(sed -n 's/.*Recovered\ position:\s*//p' ${tmpfile})
echo "wsrep_start_position: $wsrep_start_position"


rm  ${tmpfile}

# Stop without position
if test -z ${wsrep_start_position}; then
	echo "No wsrep position"
	exit 4
fi

# Configure
sed -i "s/{{XTRABACKUP_PASSWORD}}/$XTRABACKUP_PASSWORD/g" /etc/mysql/conf.d/galera.cnf
sed -i "s/{{WSREP_START_POSITION}}/$wsrep_start_position/g" /etc/mysql/conf.d/galera.cnf

# Change privilege
chown mysql:mysql $mount_path
chown mysql:mysql $data_path

python /src/join_cluster.py

while :
do
	sleep 1
done

