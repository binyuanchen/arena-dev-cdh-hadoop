# TODO
# this tool is used to run on kdc to re-create user/service principals and their keytabs
#

#!/bin/sh

# service principals (now host of the service is not part of the authN)
ZOOKEEPER=zookeeper
HDFS=hdfs
MAPRED=mapre

# user principals
ZOOKEEPER_ADMIN=zkadmin

# separate keytab files

# merged keytab files , depending a client node is accessing what
# TODO