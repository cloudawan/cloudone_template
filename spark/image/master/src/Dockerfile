FROM ubuntu:14.04
MAINTAINER Yu-Chen Chang <edcyc.tw@gmail.com>

# Install curl
RUN apt-get update
RUN apt-get install -y curl

# Install add-apt-repository
RUN apt-get update
RUN apt-get -y install software-properties-common

# Install Java 8
RUN add-apt-repository ppa:webupd8team/java
RUN apt-get update
RUN echo debconf shared/accepted-oracle-license-v1-1 select true | debconf-set-selections
RUN apt-get install -y oracle-java8-installer

# Install spark
RUN mkdir /src
RUN curl -s http://d3kbcqa49mib13.cloudfront.net/spark-2.0.0-bin-hadoop2.7.tgz  | tar -zxv -C /src
RUN mv /src/spark-2.0.0-bin-hadoop2.7 /src/spark

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
# 7077: Master
# 8080: Master GUI
EXPOSE 7077 8080

# Run
RUN chmod a+x /src/run.sh
CMD ["/src/run.sh"]
