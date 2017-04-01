FROM centos:centos7
MAINTAINER Binyuan Chen "binyuanchen@gmail.com"

ENV PATH $PATH:/usr/local/nginx/sbin

EXPOSE 1935
EXPOSE 80

RUN yum clean all && \
    yum update -y && \
    yum -y install gcc gcc-c++ make zlib-devel pcre-devel openssl-devel sudo tar unzip vim wget && \
    mkdir /src && mkdir /logs && \
    cd /src && wget http://nginx.org/download/nginx-1.11.5.tar.gz && tar zxf nginx-1.11.5.tar.gz && rm nginx-1.11.5.tar.gz && \
    cd /src/nginx-1.11.5 && ./configure --with-stream --conf-path=/config/nginx.conf --error-log-path=/logs/error.log --http-log-path=/logs/access.log && make && make install

ADD nginx.conf /config/nginx.conf
ADD bootstrap.sh /

CMD "/bootstrap.sh"
