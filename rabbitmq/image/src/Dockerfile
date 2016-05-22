FROM    centos:centos6

# Download additional repositories
RUN rpm -ivh http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm

# Install for Rabbitmq
RUN yum install -y initscripts

# Install for Rabbitmq
RUN yum install -y logrotate

# Download pip
RUN yum install -y python-pip
# Install python httplib2
RUN pip install httplib2
# Install python yaml
RUN pip install pyyaml

# Bundle app source
COPY . /src

# Install Erlang
RUN rpm -ivh /src/erlang-17.4-1.el6.x86_64.rpm

# Install Rabbitmq
RUN rpm -ivh /src/rabbitmq-server-3.5.2-1.noarch.rpm

# CHMOD
RUN chmod a+x /src/run.sh

EXPOSE  5672
CMD ["bash", "/src/run.sh"]
