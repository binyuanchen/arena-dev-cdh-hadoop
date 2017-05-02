package org.arena_dev_cdh_hadoop.pig;

import org.apache.hadoop.conf.Configuration;
import org.apache.pig.ExecType;
import org.apache.pig.PigServer;
import org.apache.pig.impl.PigContext;

import java.io.ByteArrayInputStream;

/**
 * Before running this example, you need to run the HBaseClientSimpleExample.java first. The pig script in
 * this example reads the HBase table ns1:UserData that is created by HBaseClientSimpleExample.java example.
 *
 * To run this example from command line using maven:
 *
 * mvn exec:java -DHADOOP_USER_NAME=appadmin -Dexec.mainClass=org.arena_dev_cdh_hadoop.pig.PigSimpleExample
 *
 * This example runs a pig script that counts how many rows are in the HBase table ns1:UserData
 */
public class PigSimpleExample {
    public static void main(String[] args) throws Exception {
        /**
         * The pig script. To verify your script is working before calling it from Java client,
         * you can first test it inside CDH using command line.
         */
        String script1 = "rmf /tmp/user_data_count\n" +
                "data = LOAD 'hbase://ns1:UserData' USING org.apache.pig.backend.hadoop.hbase.HBaseStorage('F:*', '-loadKey true') as (data_key:CHARARRAY, data_value:MAP[]);\n" +
                "data_group = GROUP data ALL;\n" +
                "data_count = FOREACH data_group GENERATE COUNT(data);\n" +
                "STORE data_count INTO '/tmp/user_data_count' USING PigStorage();";

        // another script
//        String script1 = "rs = LOAD '/tmp/user_data_count' AS (f1:int);" +
//                "DUMP rs;";

        // yet another script
//        String script1 = "rmf /appuser1_data/ttt;" +
//                "rs = LOAD '/appuser1_data' AS (x:CHARARRAY);" +
//                "STORE rs INTO '/appuser1_data/ttt';";

        final Configuration conf = new Configuration();

        conf.set("pig.use.overriden.hadoop.configs", "true");

        conf.set("dfs.client.use.datanode.hostname", "true");

        /**
         * The name of the pig job, you name it, it is optional
         */
        conf.set(PigContext.JOB_NAME, "user_data_count_job");

        /**
         * These configurations assume the HDFS server is in HA mode. If you are
         * running this example against the arena-dev-cdh-hadoop cluster, config_3.json
         * is creating the cluster with HDFS HA mode.
         */
        conf.set("fs.defaultFS", "hdfs://nameservice1");
        conf.set("dfs.ha.namenodes.nameservice1", "namenode1,namenode2");
        conf.set("dfs.namenode.rpc-address.nameservice1.namenode1", "cmc1.net1:8020");
        conf.set("dfs.namenode.rpc-address.nameservice1.namenode2", "cmc2.net1:8020");
        conf.set("dfs.client.failover.proxy.provider.nameservice1",
                "org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider");
        conf.set("dfs.nameservices", "nameservice1");

        /**
         * These configurations assume the MR1 JobTracker is in HA mode. If you are
         * running this example against the arena-dev-cdh-hadoop cluster, config_3.json
         * is creating the cluster with MR1 JobTracker HA mode.
         */
        conf.set("mapred.job.tracker", "logicaljt");
        conf.set("mapred.jobtrackers.logicaljt", "jobtracker1,jobtracker2");
        conf.set("mapred.jobtracker.rpc-address.logicaljt.jobtracker1", "cmc1:8021");
        conf.set("mapred.jobtracker.rpc-address.logicaljt.jobtracker2", "cmc2:8021");
        conf.set("mapred.client.failover.proxy.provider.logicaljt",
                "org.apache.hadoop.mapred.ConfiguredFailoverProxyProvider");

        /**
         * This is needed for script1, as script1 access HBase
         */
        conf.set("hbase.zookeeper.quorum", "cmc1:2181,cmc2:2181,cmc3:2181");

        /**
         * optional, not required for connection
         */
        conf.set("mapred.map.tasks", "2");
        conf.set("mapred.reduce.tasks", "2");
        conf.set("hbase.defaults.for.version.skip", "true");
        conf.set("hbase.client.pause", "2000");
        conf.set("hbase.client.retries.number", "3");
        conf.set("hbase.rpc.timeout", "5000");

        /**
         * creating a pig server which runs in mapreduce mode
         */
        PigServer pigServer = new PigServer(ExecType.MAPREDUCE, conf);

        /**
         * registering the pig script will run it
         */
        try {
            pigServer.registerScript(new ByteArrayInputStream(script1.getBytes()));
        } finally {
            pigServer.shutdown();
        }
    }
}
