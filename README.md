# arena-dev-cdh-hadoop

As a Hadoop user and a developer, I constantly feel the need to connect my application code to a CDH Hadoop cluster. My initial try was to connect an existing Hadoop cluster in Jenkins or in QE environment. Soon I found out that this approach is not practical. For example, my applications writes into the cluster and sometimes this confuses the automated tests. Another example, sometimes I try to do destructive tests on Hadoop cluster such as restarting HBASE region server on one node in the middle of writing data into it, or shutting down one running Spark container to see how my spark application behaves.

In summary, I want such a Hadoop cluster that,

* it is running on my local, so it is dedicated to my use,
* it is a cluster with more than one node,
* I can change the server side however I want,
* if I screw this cluster, I can quickly spawn another one, exactly the same as before,
* the cluster is generic and standard enough in the sense after I verify my application code against it, it takes minimal modifications to against production clusters,
* it doesn't need to be ready for performance testing or production usage.

Finally I decide to build one for myself, this is Arena-dev-cdh-hadoop: a three-node (yes, only 3, no more and no less) CDH Hadoop cluster running on your local Mac machine.

I decide to open source it and hope it is in any help for you.

Please refer to my blog talking about how to create such a CDH Hadoop cluster, at
https://binyuanchen.github.io/posts/update/2017/04/01/introduction-to-arena-dev-cdh-hadoop.html

This project is for developers who work on application code that accesses CDH Hadoop system. It helps you create a three-node CDH Hadoop cluster running on your local Mac machine.

Some highlight of such a cluster,

* it runs on your local Mac,
* it is a cluster with more than one node, all nodes are running as docker containers,
* if you screw the cluster, you can quickly setup a new one using deployer script (python),
* the cluster is generic enough in the sense that once you verified your application code works well with the cluster, it doesn't take much effort to make it work with your production cluster,
* the cluster is not for performance or production use.

With such a cluster, you no longer worry about confusions caused when your application code writes into a Jenkins or automation testing Hadoop cluster which is shared by automation tests.

