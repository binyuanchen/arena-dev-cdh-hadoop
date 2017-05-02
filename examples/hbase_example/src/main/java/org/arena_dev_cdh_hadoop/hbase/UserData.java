package org.arena_dev_cdh_hadoop.hbase;

/**
 * A row of the HBase table
 */
public class UserData {
    private String key;
    private String val1;
    private String val2;
    private String val3;

    public String getKey() {
        return key;
    }

    public void setKey(String key) {
        this.key = key;
    }

    public String getVal1() {
        return val1;
    }

    public void setVal1(String val1) {
        this.val1 = val1;
    }

    public String getVal2() {
        return val2;
    }

    public void setVal2(String val2) {
        this.val2 = val2;
    }

    public String getVal3() {
        return val3;
    }

    public void setVal3(String val3) {
        this.val3 = val3;
    }

    @Override
    public String toString() {
        return "UserData{" +
                "key='" + key + '\'' +
                ", val1='" + val1 + '\'' +
                ", val2='" + val2 + '\'' +
                ", val3='" + val3 + '\'' +
                '}';
    }
}
