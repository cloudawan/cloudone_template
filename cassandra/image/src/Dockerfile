FROM ubuntu:14.04
MAINTAINER Yu-Chen Chang <edcyc.tw@gmail.com>

ENV CASSANDRA_VERSION 2.2.4

# Install curl
RUN apt-get install -y curl

# Setup repository
RUN apt-key adv --keyserver ha.pool.sks-keyservers.net --recv-keys 514A2AD631A57A16DD0047EC749D6EEC0353B12C
RUN echo 'deb http://www.apache.org/dist/cassandra/debian 22x main' >> /etc/apt/sources.list.d/cassandra.list

# install packages
RUN apt-get update
RUN apt-get install -y cassandra="$CASSANDRA_VERSION"

# For python script
# Install python
RUN apt-get -y install python
# Download pip
RUN apt-get -y install python-pip
# Install python httplib2
RUN pip install httplib2
# Install python yaml
RUN pip install pyyaml
	
# Bundle app source
COPY . /src

# Expose port
# 7000: intra-node communication
# 7001: TLS intra-node communication
# 7199: JMX
# 9042: CQL
# 9160: thrift service
EXPOSE 7000 7001 7199 9042 9160

# Mount
VOLUME /var/lib/cassandra

# Run
RUN chmod a+x /src/run.sh
CMD ["/src/run.sh"]
