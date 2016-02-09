FROM ubuntu:14.04
MAINTAINER Yu-Chen Chang <edcyc.tw@gmail.com>

ENV ELASTICSEARCH_VERSION 2.1.0

# Install curl
RUN apt-get -y install curl

# To run as non root
RUN gpg --keyserver ha.pool.sks-keyservers.net --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4
RUN arch="$(dpkg --print-architecture)" \
	&& set -x \
	&& curl -o /usr/local/bin/gosu -fSL "https://github.com/tianon/gosu/releases/download/1.3/gosu-$arch" \
	&& curl -o /usr/local/bin/gosu.asc -fSL "https://github.com/tianon/gosu/releases/download/1.3/gosu-$arch.asc" \
	&& gpg --verify /usr/local/bin/gosu.asc \
	&& rm /usr/local/bin/gosu.asc \
	&& chmod +x /usr/local/bin/gosu

# Install add-apt-repository
RUN apt-get update
RUN apt-get -y install software-properties-common

# Install Java 8
RUN add-apt-repository ppa:webupd8team/java
RUN apt-get update
RUN echo debconf shared/accepted-oracle-license-v1-1 select true | debconf-set-selections
RUN apt-get install -y oracle-java8-installer

# Setup repository
RUN wget -qO - https://packages.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
RUN echo "deb http://packages.elastic.co/elasticsearch/2.x/debian stable main" | sudo tee -a /etc/apt/sources.list.d/elasticsearch-2.x.list

# Install packages
RUN apt-get update 
RUN apt-get install -y elasticsearch="$ELASTICSEARCH_VERSION"

ENV PATH /usr/share/elasticsearch/bin:$PATH

# Move location
RUN mv /var/lib/elasticsearch /usr/share/elasticsearch/data
RUN mv /etc/elasticsearch /usr/share/elasticsearch/config
RUN mv /var/log/elasticsearch /usr/share/elasticsearch/logs

# Change owner
RUN chown elasticsearch:elasticsearch /usr/share/elasticsearch/data
RUN chown elasticsearch:elasticsearch /usr/share/elasticsearch/config
RUN chown elasticsearch:elasticsearch /usr/share/elasticsearch/logs

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
EXPOSE 9200 9300

# Mount
VOLUME /usr/share/elasticsearch/data

# Run
RUN chmod a+x /src/run.sh
CMD ["/src/run.sh"]
