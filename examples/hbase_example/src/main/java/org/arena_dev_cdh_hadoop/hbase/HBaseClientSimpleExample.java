package org.arena_dev_cdh_hadoop.hbase;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.hbase.HBaseConfiguration;
import org.apache.hadoop.security.UserGroupInformation;
import org.apache.hadoop.security.authentication.util.KerberosName;

/**
 * To run this example from command line using maven:
 *
 * mvn exec:java -DHADOOP_USER_NAME=appadmin -Dexec.mainClass=org.arena_dev_cdh_hadoop.hbase.HBaseClientSimpleExample
 *
 * This example creates a HBase namespace, a table in it, 1 column families, with 3 column qualifiers.
 * <p>
 * Write 100 records, and read them out.
 */
public class HBaseClientSimpleExample {
    public static void main(String[] args) throws Exception {
        HBaseServiceManager hBaseServiceManager = new HBaseServiceManager();

        Configuration conf = HBaseConfiguration.create();

        conf.set("hbase.zookeeper.quorum", "cmc1:2181,cmc2:2181,cmc3:2181");

        conf.set("hbase.client.pause", "2000");
        conf.set("hbase.client.retries.number", "3");
        conf.set("hbase.rpc.timeout", "5000");

        try {
            hBaseServiceManager.init(conf);

            // put NUM into each region
            final int NUM = 100;

            String[] ps = {"a", "g", "o"};
            for (String p : ps) {
                for (int i = 0; i < NUM; i++) {
                    String key = p + (i + 1);
                    String val1 = p + "-" + (i + 1);
                    String val2 = p + "-" + (i + 1);
                    String val3 = p + "-" + (i + 1);
                    UserData userData = new UserData();
                    userData.setKey(key);
                    userData.setVal1(val1);
                    userData.setVal2(val2);
                    userData.setVal3(val3);
                    hBaseServiceManager.save(userData);
                }
            }

            for (String p : ps) {
                for (int i = 0; i < NUM; i++) {
                    String key = p + (i + 1);
                    UserData userData = hBaseServiceManager.get(key);
                    System.out.println(userData);
                }
            }
        } finally {
            hBaseServiceManager.close();
        }
    }
}
