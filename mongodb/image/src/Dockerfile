FROM ubuntu:14.04
MAINTAINER Yu-Chen Chang <edcyc.tw@gmail.com>

# Install curl
RUN apt-get install -y curl

# Setup repository
RUN sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927
RUN echo "deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.2 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.2.list

# install packages
RUN apt-get update
RUN apt-get install -y mongodb-org=3.2.4 mongodb-org-server=3.2.4 mongodb-org-shell=3.2.4 mongodb-org-mongos=3.2.4 mongodb-org-tools=3.2.4

# For python script
# Install python
RUN apt-get -y install python
# Download pip
RUN apt-get -y install python-pip
# Install python httplib2
RUN pip install httplib2
	
# Bundle app source
COPY . /src

# Expose port
EXPOSE 27017

# Mount
VOLUME /var/lib/mongodb

# Run
RUN chmod a+x /src/run.sh
CMD ["/src/run.sh"]
