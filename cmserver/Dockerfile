FROM centos:centos7
MAINTAINER Binyuan Chen "binyuanchen@gmail.com"

ENV PARCEL_CACHE_LOC /opt/cloudera/parcel-cache
ENV JDK_VERSION 1.8.0_131
ENV JDK_RPM_URL http://download.oracle.com/otn-pub/java/jdk/8u131-b11/d54c1d3a095b4ff2b6607d096fa80163/jdk-8u131-linux-x64.rpm
ENV JCE_URL http://download.oracle.com/otn-pub/java/jce/8/jce_policy-8.zip
ENV CDH_VERSION 5.8.3
ENV PARCEL_DIR_URL http://archive.cloudera.com/cdh5/parcels/5.8.3/
ENV PARCEL_NAME CDH-5.8.3-1.cdh5.8.3.p0.2-el7.parcel
ENV TERM=xterm

# Package installation
RUN yum clean all && \
    yum update -y && \
    yum install -y openssh-server openssh-clients sudo tar unzip vim wget epel-release && \
    yum install -y krb5-libs krb5-workstation net-tools ntp openldap-clients python-pip xmlstarlet jq nc telnet sshfs mlocate lsof && \
    yum install -y nmap && \
    wget --progress=dot:giga -O /tmp/jdk-$JDK_VERSION-x64.rpm --no-cookies --no-check-certificate -c \
        --header "Cookie: oraclelicense=accept-securebackup-cookie" $JDK_RPM_URL && \
    rpm -Uhv /tmp/jdk-$JDK_VERSION-x64.rpm && rm -f /tmp/jdk-$JDK_VERSION-x64.rpm && \
    wget --progress=dot:giga -O /tmp/JCE.zip --no-cookies --no-check-certificate -c \
        --header "Cookie: gpw_e24=http%3A%2F%2Fwww.oracle.com%2F; oraclelicense=accept-securebackup-cookie" $JCE_URL && \
    unzip -d /tmp/ /tmp/JCE.zip && \
    cp -vf /tmp/UnlimitedJCEPolicy*/US_export_policy.jar /usr/java/jdk$JDK_VERSION/jre/lib/security/ && \
    cp -vf /tmp/UnlimitedJCEPolicy*/local_policy.jar /usr/java/jdk$JDK_VERSION/jre/lib/security/ && \
    rm -rf /tmp/* && \
    wget --progress=dot:giga -O /etc/yum.repos.d/cloudera-manager.repo \
        http://archive.cloudera.com/cm5/redhat/7/x86_64/cm/cloudera-manager.repo && \
    rpm --import http://archive.cloudera.com/cdh5/redhat/7/x86_64/cdh/RPM-GPG-KEY-cloudera && \
    sed -i "s/^baseurl.*/baseurl=http:\/\/archive.cloudera.com\/cm5\/redhat\/7\/x86_64\/cm\/$CDH_VERSION\//" /etc/yum.repos.d/cloudera-manager.repo && \
    yum install --nogpgcheck localinstall -y \
        cloudera-manager-daemons \
        cloudera-manager-server \
        cloudera-manager-server-db-2 \
        cloudera-manager-agent && \
    wget --progress=dot:giga -P $PARCEL_CACHE_LOC $PARCEL_DIR_URL/$PARCEL_NAME && \
    wget --progress=dot:giga -P $PARCEL_CACHE_LOC $PARCEL_DIR_URL/$PARCEL_NAME.sha1 && \
    cp -p $PARCEL_CACHE_LOC/$PARCEL_NAME.sha1 $PARCEL_CACHE_LOC/$PARCEL_NAME.sha && \
    for i in /opt/cloudera/parcel-cache/*; do ln -sf $i /opt/cloudera/parcel-repo/$(basename $i); done && \
    sed -i 's/Defaults.*requiretty.*$/#Defaults requiretty/' /etc/sudoers && \
    ssh-keygen -A && \
    echo "root:root" | chpasswd && \
    mkdir /var/log/supervisor && \
    ln -s /usr/lib64/cmf/agent/build/env/bin/supervisorctl /usr/bin/supervisorctl && \
    ln -s /usr/lib64/cmf/agent/build/env/bin/supervisord /usr/bin/supervisord && \
    mkdir /cmserverscripts && \
    rm -rf /etc/security/limits.d/cloudera-scm*.conf && \
    ln -s /etc/init.d/cloudera-scm-server-db /usr/sbin/cloudera-scm-server-db && \
    ln -s /etc/init.d/cloudera-scm-server /usr/sbin/cloudera-scm-server && \
    ln -s /etc/init.d/cloudera-scm-agent /usr/sbin/cloudera-scm-agent

ADD supervisord.conf /etc/
ADD launcher.sh /cmserverscripts/
ADD checkdisk.sh /usr/local/bin/

CMD ["supervisord", "-n"]
