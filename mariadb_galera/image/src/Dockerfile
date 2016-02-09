FROM ubuntu:14.04
MAINTAINER Yu-Chen Chang <edcyc.tw@gmail.com>

ENV DEBIAN_FRONTEND noninteractive

# Setup repository
RUN echo "deb http://archive.ubuntu.com/ubuntu trusty main universe" > /etc/apt/sources.list
RUN apt-key adv --recv-keys --keyserver hkp://keyserver.ubuntu.com:80 0xcbcb082a1bb943db
RUN echo 'deb http://ftp.hosteurope.de/mirror/mariadb.org/repo/10.0/ubuntu trusty main' >> /etc/apt/sources.list
RUN apt-get -y update

# install packages
RUN apt-get -y --no-install-recommends --no-install-suggests install host socat unzip ca-certificates wget
RUN apt-get -y install mariadb-galera-server-10.0 galera-3 mariadb-client xtrabackup

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

# configure mysqld
RUN sed -i 's/#? *bind-address/# bind-address/' /etc/mysql/my.cnf
RUN sed -i 's/#? *log-error/# log-error/' /etc/mysql/my.cnf
RUN cp -f /src/utf8.cnf /etc/mysql/conf.d/utf8.cnf
RUN cp -f /src/galera.cnf /etc/mysql/conf.d/galera.cnf
RUN chmod 0644 /etc/mysql/conf.d/utf8.cnf
RUN chmod 0644 /etc/mysql/conf.d/galera.cnf


# Expose port
EXPOSE 3306 4444 4567 4568

# Mount
VOLUME ["/var/lib/mysql"]

# Run
RUN chmod a+x /src/run.sh
CMD ["/src/run.sh"]