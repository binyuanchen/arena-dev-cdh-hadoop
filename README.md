# arena-dev-cdh-hadoop

This project is for developers who work on application code that accesses CDH Hadoop system. It helps you create a three-node CDH Hadoop cluster running on your local Mac machine.

Some highlight of such a cluster,

* it runs on your local Mac,
* it is a cluster with more than one node, all nodes are running as docker containers,
* if you screw the cluster, you can quickly setup a new one using deployer script (python),
* the cluster is generic enough in the sense that once you verified your application code works well with the cluster, it doesn't take much effort to make it work with your production cluster,
* the cluster is not for performance or production use.

With such a cluster, you no longer worry about confusions caused when your application code writes into a Jenkins or automation testing Hadoop cluster which is shared by automation tests.

To see how to create such a cluster, refer to blog at: https://binyuanchen.github.io/posts/update/2017/04/01/introduction-to-arena-dev-cdh-hadoop.html
