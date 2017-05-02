package org.arena_dev_cdh_hadoop.hbase;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.hbase.*;
import org.apache.hadoop.hbase.client.*;
import org.apache.hadoop.hbase.util.Bytes;
import org.apache.hadoop.hbase.util.RegionSplitter;

import java.util.Arrays;
import java.util.Iterator;
import java.util.Map;
import java.util.NavigableMap;

public class HBaseServiceManager {
    // a single connection is cached
    private Connection connection;

    // a fixed namespace name
    public static final String NS_NAME = "ns1";

    // a fixed table name
    public static final String TABLE_NAME = NS_NAME + ":" + "UserData";

    // one fixed CF
    public static final String CF_NAME = "F";

    // 3 fixed C qualifiers
    public static final String C_NAME1 = "C1";
    public static final String C_NAME2 = "C2";
    public static final String C_NAME3 = "C3";

    public HBaseServiceManager() throws Exception {
    }


    public void init(Configuration conf) throws Exception {
        if (conf == null) {
            // assume xml in classpath
            this.connection = ConnectionFactory.createConnection();
        } else {
            this.connection = ConnectionFactory.createConnection(conf);
        }

        // create ns if not exist
        Admin admin = this.connection.getAdmin();
        try {
            admin.getNamespaceDescriptor(NS_NAME);
        } catch (NamespaceNotFoundException e) {
            System.out.println("will create namespace: " + NS_NAME);
            NamespaceDescriptor nsDesc = NamespaceDescriptor.create(NS_NAME).build();
            admin.createNamespace(nsDesc);
        }

        // create table if not exist
        try {
            admin.getTableDescriptor(TableName.valueOf(TABLE_NAME));
        } catch (TableNotFoundException e) {
            System.out.println("will create table: " + TABLE_NAME);

            HColumnDescriptor hColumnDescriptor = new HColumnDescriptor(CF_NAME);
            HTableDescriptor hTableDescriptor = new HTableDescriptor(TableName.valueOf(TABLE_NAME));
            hTableDescriptor.addFamily(hColumnDescriptor);

            // pre-spit of table into 3 regions
            byte[][] splits = {Bytes.toBytes("f"), Bytes.toBytes("n")};

            admin.createTable(hTableDescriptor, splits);
        }
    }

    public UserData get(String key) throws Exception {
        Table table = this.connection.getTable(TableName.valueOf(TABLE_NAME));
        try {
            Get get = new Get(Bytes.toBytes(key));
            Result result = table.get(get);
            if (result.isEmpty()) {
                return null;
            }

            UserData userData = new UserData();
            userData.setKey(key);

            NavigableMap<byte[], NavigableMap<byte[], NavigableMap<Long, byte[]>>> mapOfMaps = result.getMap();
            for (Map.Entry<byte[], NavigableMap<byte[], NavigableMap<Long, byte[]>>> entry0 : mapOfMaps.entrySet()) {
                String columnFamily = Bytes.toString(entry0.getKey());
                if (!columnFamily.equals(CF_NAME)) {
                    throw new Exception("columnFamily is not recognized: " + columnFamily);
                }
                NavigableMap<byte[], NavigableMap<Long, byte[]>> map = entry0.getValue();
                for (Map.Entry<byte[], NavigableMap<Long, byte[]>> entry : map.entrySet()) {
                    String columnQualifier = Bytes.toString(entry.getKey());
                    Iterator<byte[]> it = entry.getValue().values().iterator();
                    if (it.hasNext()) {
                        byte[] val = it.next();
                        if (columnQualifier.equals(C_NAME1)) {
                            userData.setVal1(Bytes.toString(val));
                        } else if (columnQualifier.equals(C_NAME2)) {
                            userData.setVal2(Bytes.toString(val));
                        } else if (columnQualifier.equals(C_NAME3)) {
                            userData.setVal3(Bytes.toString(val));
                        } else {
                            throw new Exception("columnQualifier is not recognized: " + columnQualifier);
                        }
                    }
                }
            }

            return userData;
        } finally {
            table.close();
        }
    }

    public void save(UserData userData) throws Exception {
        Table table = this.connection.getTable(TableName.valueOf(TABLE_NAME));
        try {
            Put put = new Put(Bytes.toBytes(userData.getKey()));
            put.addColumn(Bytes.toBytes(CF_NAME), Bytes.toBytes(C_NAME1), Bytes.toBytes(userData.getVal1()));
            put.addColumn(Bytes.toBytes(CF_NAME), Bytes.toBytes(C_NAME2), Bytes.toBytes(userData.getVal2()));
            put.addColumn(Bytes.toBytes(CF_NAME), Bytes.toBytes(C_NAME3), Bytes.toBytes(userData.getVal3()));

            table.put(put);
        } finally {
            table.close();
        }
    }

    public void close() throws Exception {
        this.connection.close();
    }
}
