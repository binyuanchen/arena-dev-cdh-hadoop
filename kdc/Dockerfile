FROM alpine:3.3
MAINTAINER Binyuan Chen "binyuanchen@gmail.com"


ENV KRB5_KDC_PROFILE /usr/local/var/krb5kdc/kdc.conf

RUN apk add --update drill krb5-server haveged openrc && \
    rm -rf /var/cache/apk/* && \
    # configure and run the openrc service as pid 1
    mkdir -p /etc/apk && echo "http://alpine.gliderlabs.com/alpine/v3.3/main" > /etc/apk/repositories && \
    # let openrc know it is inside a container
    sed -i 's/#rc_sys=""/rc_sys="lxc"/g' /etc/rc.conf && \
    # let openrc knows loopback and net already exist
    echo 'rc_provide="loopback net"' >> /etc/rc.conf && \
    sed -i 's/^#\(rc_logger="YES"\)$/\1/' /etc/rc.conf && \
    # ttys is not available unless this container runs with privileged mode
    sed -i '/tty/d' /etc/inittab && \
    # can't set hostname since docker sets it
    sed -i 's/hostname $opts/# hostname $opts/g' /etc/init.d/hostname && \
    # can't mount tmpfs since not privileged
    sed -i 's/mount -t tmpfs/# mount -t tmpfs/g' /lib/rc/sh/init.sh && \
    # can't do cgroups
    sed -i 's/cgroup_add_service /# cgroup_add_service /g' /lib/rc/sh/openrc-run.sh && \
    # this needs --privileged=true to run this container, this actually writes to host env
    #echo 2048 > /proc/sys/kernel/random/write_wakeup_threshold && \
    # add haveged as daemon service at 'default' runlevel
    rc-update add haveged default && \
    # add the local service kdc_init_service.start defined above
    rc-update add local default
    # can not do below as kdb create must happen before them
    #rc-update add krb5kdc default && \
    #rc-update add krb5kadmind default

ADD krb5.conf.server.example /etc/krb5.conf
#ADD kdc.conf.server.example /var/krb5kdc/kdc.conf
ADD kdc.conf.server.example /usr/local/var/krb5kdc/kdc.conf
ADD kdc.conf.server.example /var/krb5kdc/kdc.conf
ADD kdc.conf.server.example /var/lib/krb5kdc/kdc.conf
ADD kdc.conf.server.example /etc/kdc.conf
ADD kadm5.acl /var/lib/krb5kdc/kadm5.acl
ADD kdc_init_service.start /etc/local.d/

EXPOSE	88 749

CMD ["/sbin/init"]
