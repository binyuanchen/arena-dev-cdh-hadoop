package org.arena_dev_cdh_hadoop.spark;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.hbase.HBaseConfiguration;
import org.apache.hadoop.hbase.TableName;
import org.apache.hadoop.hbase.client.Result;
import org.apache.hadoop.hbase.client.Scan;
import org.apache.hadoop.hbase.io.ImmutableBytesWritable;
import org.apache.hadoop.hbase.spark.JavaHBaseContext;
import org.apache.hadoop.hbase.util.Bytes;
import org.apache.spark.SparkConf;
import org.apache.spark.api.java.JavaRDD;
import org.apache.spark.api.java.JavaSparkContext;
import org.apache.spark.api.java.function.Function;
import scala.Tuple2;

/**
 * Before running this example, you need to run the HBaseClientSimpleExample.java first. The application in
 * this example reads the HBase table ns1:UserData that is created by HBaseClientSimpleExample.java example.
 * <p>
 * This example shows how to create a spark application uber jar, and execute the application in CDH
 * using spark-submit command line tools.
 * <p>
 * To run this example:
 * 1. Copy the target/spark_example-0.2.jar file to the /tmp/ folder of container cmc1
 * 2. On cmc1 container, run
 * su - appadmin -c "spark-submit --jars /opt/cloudera/parcels/CDH/jars/hbase-spark-1.2.0-cdh5.7.1.jar --driver-memory 64M --executor-memory 64M --num-executors 3 --class org.arena_dev_cdh_hadoop.spark.ScanUserDataSparkSimpleApp --deploy-mode cluster --master yarn /tmp/spark_example-0.2.jar"
 */

public class ScanUserDataSparkSimpleApp {

    public static void main(String[] args) {

        JavaSparkContext jsc = null;
        try {
            final Configuration conf = HBaseConfiguration.create();
            conf.set("hbase.zookeeper.quorum", "cmc1:2181,cmc2:2181,cmc3:2181");

            // optional
            conf.set("hbase.client.pause", "5000");
            conf.set("hbase.client.retries.number", "1");
            conf.set("hbase.rpc.timeout", "10000");

            conf.set("hbase.client.scanner.caching", "100");
            SparkConf sparkConf = new SparkConf().setAppName("ScanUserDataSparkSimpleApp");
            sparkConf.set("spark.network.timeout", "5");

            jsc = new JavaSparkContext(sparkConf);

            JavaHBaseContext hBaseContext = new JavaHBaseContext(jsc, conf);

            Scan scan = new Scan();

            JavaRDD<Tuple2<ImmutableBytesWritable, Result>> javaRDD =
                    hBaseContext.hbaseRDD(TableName.valueOf("ns1:UserData"), scan);

            long count = javaRDD.map(new ScanConvertFunction()).collect().size();

            System.out.println("Table ns1:UserData COUNT=" + count);
        } catch (Exception e) {
            throw new RuntimeException(e);
        } finally {
            jsc.stop();
        }
    }

    private static class ScanConvertFunction implements Function<Tuple2<ImmutableBytesWritable, Result>, String> {
        public String call(Tuple2<ImmutableBytesWritable, Result> t) throws Exception {
            String rs = Bytes.toString(t._1().copyBytes());
            System.out.println("ScanConvertFunction => " + rs);
            return rs;
        }
    }
}
