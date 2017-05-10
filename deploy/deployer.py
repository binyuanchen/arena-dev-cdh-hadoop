#!/usr/bin/env python

import sys
import json
import time
import optparse
import paramiko
import cmconfig
import restutil
from collections import OrderedDict
import segment

class CMClusterDeployer(object):

    def __init__(self,
                 cm_user='admin',
                 cm_pass='admin',
                 cm_api_entrypoint=None,
                 cm_api_version='v12'
                 ):
        self.cm_user = cm_user
        self.cm_pass = cm_pass
        self.cm_api_entrypoint = cm_api_entrypoint
        self.cm_api_version = cm_api_version

        self.rest_util = restutil.RestUtil(self.cm_user, self.cm_pass)

    ##################################################
    # util methods
    ##################################################

    def _wait_for_command_finish(self, cmd_id, interval=2):
        api_url = "http://%s/api/%s/commands/%s" % (self.cm_api_entrypoint, self.cm_api_version, cmd_id)
        cmd = self.rest_util.get(url=api_url)
        # The 'success' field may not be available immediately after state becomes 'inactive',
        # for a short while it may be None
        while cmd['active'] or cmd['success'] is None:
            # TODO needs to re-implement
            time.sleep(interval)
            cmd = self.rest_util.get(url=api_url)
        return cmd['success']

    def _get_cdh_parcel_stage(self, cluster_name, cdh_parcel):
        '''return the stage information of given cdh parcel'''
        api_url = "http://%s/api/%s/clusters/%s/parcels" % \
                  (self.cm_api_entrypoint, self.cm_api_version, cluster_name)
        parcel_list = self.rest_util.get(url=api_url)
        for parcel in parcel_list['items']:
            if parcel['version'] == cdh_parcel:
                return parcel['stage']
        return None

    def _get_cdh_parcel(self, cluster_name, cdh_full_version):
        '''return the version (parcel name) of the 1st DOWNLOADED parcel of
        a given cluster, matching the given cdh full version'''
        api_url = "http://%s/api/%s/clusters/%s/parcels" % \
                  (self.cm_api_entrypoint, self.cm_api_version, cluster_name)
        parcel_list = self.rest_util.get(url=api_url)
        for parcel in parcel_list['items']:
            if parcel['stage'] == 'DOWNLOADED' and cdh_full_version in parcel['version']:
                return parcel['version']
        return None

    def _download_parcel_on_cluster(self, cluster_name=None, cdh_parcel=None):
        print 'download_parcel_on_cluster - BEGIN'
        api_url = "http://%s/api/%s/clusters/%s/parcels/products/CDH/versions/%s/commands/startDownload" % \
                  (self.cm_api_entrypoint, self.cm_api_version, cluster_name, cdh_parcel)
        self.rest_util.post(url=api_url)
        # check if parcel is distributed
        stage = None
        while not stage or stage != 'DOWNLOADED':
            # as far as deloyer's concern, if already activated, skip
            if stage == 'DISTRIBUTED' or stage == 'ACTIVATED':
                print 'cdh %s on cluster %s is already DISTRIBUTED or ACTIVATED' % (cdh_parcel, cluster_name)
                return
            time.sleep(2)
            stage = self._get_cdh_parcel_stage(cluster_name, cdh_parcel)
            print 'download_parcel_on_cluster - parcel %s current stage is %s' % (cdh_parcel, stage)
        print 'download_parcel_on_cluster - DONE'

    def get_all_host_info(self):
        '''return hosts (cmserver, cmagents) name to [id, ip] mapping'''
        api_url = "http://%s/api/%s/hosts" % (self.cm_api_entrypoint, self.cm_api_version)
        response_body = self.rest_util.get(url=api_url)
        all_hosts_info = dict(
                [(host['hostname'], [host['hostId'], host['ipAddress']]) for host in response_body['items']]
        )
        return all_hosts_info

    ##################################################
    # cluster operations
    ##################################################

    def create_cluster(self, cluster_name=None, cdh_version=None, cdh_full_version=None):
        print 'create_cluster - BEGIN'
        api_url = "http://%s/api/%s/clusters" % (self.cm_api_entrypoint, self.cm_api_version)
        # is cluster existed
        response_body = self.rest_util.get(url=api_url)
        cluster_exists=False
        if response_body and response_body['items']:
            for item in response_body['items']:
                if item['displayName'] == cluster_name:
                    cluster_exists = True
        if cluster_exists:
            # skip but continue to run
            print 'create_cluster - SKIP, as cluster %s exists' % cluster_name
            return

        # create this cluster
        create_cluster_request = {
            'items' : [
                {
                    'name' : cluster_name,
                    'displayName' : cluster_name,
                    'version' : cdh_version,
                    'fullVersion' : cdh_full_version
                }
            ]
        }
        self.rest_util.post(url=api_url, body=create_cluster_request)
        print 'create_cluster - DONE'

    def install_all_hosts(self,
                          cmserver=None,
                          cmagents=None,
                          ssh_user=None,
                          ssh_pass=None,
                          ssh_port=22, # used only by cmserver to ssh into cmagents
                          cmRepoUrl="http://archive.cloudera.com/cm5/redhat/7/x86_64/cm/5.7.1",
                          gpgKeyCustomUrl="http://archive.cloudera.com/cm5/redhat/7/x86_64/cm/RPM-GPG-KEY-cloudera"):
        print 'install_all_hosts - BEGIN'
        api_url = "http://%s/api/%s/cm/commands/hostInstall" % (self.cm_api_entrypoint, self.cm_api_version)

        # collects hostnames to install as [cmc1.net1, cmc2.net1, cmc3.net1]
        hostnames_to_install = []

        if not cmserver:
            raise RuntimeError('install_all_hosts - no cmserver')
        hostnames_to_install.append(cmserver)

        if not cmagents:
            raise RuntimeError('install_all_hosts - no cmagents')
        for a in cmagents:
            hostnames_to_install.append(a)

        host_install_request = {
            "hostNames" : hostnames_to_install,
            "sshPort" : ssh_port,
            "userName" : ssh_user,
            "password" : ssh_pass,
            "parallelInstallCount" : 10,
            "cmRepoUrl" : cmRepoUrl,
            "gpgKeyCustomUrl" : gpgKeyCustomUrl,
            "javaInstallStrategy" : "NONE",
            "unlimitedJCE" : "false"
        }

        cmd = self.rest_util.post(url=api_url, body=host_install_request)
        cmd_status = self._wait_for_command_finish(cmd['id'], interval=10)
        if cmd_status:
            print 'install_all_hosts - DONE'
        else:
            print 'install_all_hosts - ERROR'
            raise RuntimeError('install_all_hosts - failed on hosts : %s' % hostnames_to_install)

    def add_hosts_to_cluster(self, cluster_name, host_ids=None):
        print 'add_hosts_to_cluster - BEGIN'
        api_url = "http://%s/api/%s/clusters/%s/hosts" %\
                  (self.cm_api_entrypoint, self.cm_api_version, cluster_name)
        response_body = self.rest_util.get(url=api_url)
        if response_body and response_body["items"]:
            # if there is any host already in the cluster, we skip this step
            if len(response_body["items"]) > 0:
                print "add_hosts_to_cluster - cluster %s already had some hosts, skip" % cluster_name
                return
        add_hosts_to_cluster_request = {
            "items" : [{"hostId" : hid} for hid in host_ids]
        }
        self.rest_util.post(url=api_url, body=add_hosts_to_cluster_request)
        print 'add_hosts_to_cluster - DONE'

    def distribute_parcel_on_cluster(self, cluster_name=None, cdh_parcel=None):
        '''call to distribute cdh parcel within the given cluster'''

        '''
        # check parcel binary availability
        stage = self._get_cdh_parcel_stage(cluster_name=cluster_name, cdh_parcel=cdh_parcel)
        if stage == None or stage == 'UNAVAILABLE':
            raise RuntimeError('missing stage of parcel %s on cluster %s' % (cdh_parcel, cluster_name))
        elif stage == 'AVAILABLE_REMOTELY':
            # download it
            self._download_parcel_on_cluster(cluster_name=cluster_name, cdh_parcel=cdh_parcel)
        else:
            print 'distribute_parcel_on_cluster - parcels %s is already available.' % cdh_parcel
            pass
        '''

        print 'distribute_parcel_on_cluster - BEGIN'
        api_url = "http://%s/api/%s/clusters/%s/parcels/products/CDH/versions/%s/commands/startDistribution" % \
                  (self.cm_api_entrypoint, self.cm_api_version, cluster_name, cdh_parcel)
        self.rest_util.post(url=api_url)
        # check if parcel is distributed
        stage = None
        while not stage or stage != 'DISTRIBUTED':
            # as far as deloyer's concern, if already activated, skip
            if stage == 'ACTIVATED':
                print 'cdh %s on cluster %s is already ACTIVATED' % (cdh_parcel, cluster_name)
                return
            time.sleep(2)
            stage = self._get_cdh_parcel_stage(cluster_name, cdh_parcel)
            print 'distribute_parcel_on_cluster - parcel %s current stage is %s' % (cdh_parcel, stage)
        print 'distribute_parcel_on_cluster - DONE'

    def activate_parcel_on_cluster(self, cluster_name=None, cdh_parcel=None):
        '''call to activate cdh parcel within the given cluster'''
        print 'activate_parcel_on_cluster - BEGIN'
        api_url = "http://%s/api/%s/clusters/%s/parcels/products/CDH/versions/%s/commands/activate" % \
                  (self.cm_api_entrypoint, self.cm_api_version, cluster_name, cdh_parcel)

        self.rest_util.post(url=api_url)
        # check if parcel is activated
        stage = None
        while not stage or stage != 'ACTIVATED':
            time.sleep(2)
            stage = self._get_cdh_parcel_stage(cluster_name, cdh_parcel)
            print 'activate_parcel_on_cluster - parcel %s current stage is %s' % (cdh_parcel, stage)
        print 'activate_parcel_on_cluster - DONE'

    def upload_cluster_config(self, json_config=None):
        print 'upload_cluster_config - BEGIN'
        api_url = "http://%s/api/%s/cm/deployment?deleteCurrentDeployment=true" % \
                  (self.cm_api_entrypoint, self.cm_api_version)
        self.rest_util.put(url=api_url, body=json_config)
        print 'upload_cluster_config - DONE'

    def firstrun_cluster(self, cluster_name=None):
        '''Perform all the steps needed to prepare each service in a cluster and start the services in order.'''
        print 'firstrun_cluster - BEGIN'
        api_url = 'http://%s/api/%s/clusters/%s/commands/firstRun' % \
                  (self.cm_api_entrypoint, self.cm_api_version, cluster_name)
        cmd = self.rest_util.post(url=api_url)
        cmd_status = self._wait_for_command_finish(cmd['id'])
        print 'firstrun_cluster - command_status = %s' % cmd_status
        if cmd_status:
            print 'firstrun_cluster - DONE'
        else:
            raise RuntimeError('firstrun_cluster - failed.')

    def start_cm(self):
        '''start the Cloudera Management Services:
        Event Server, Host Monitor, Service Monitor, Alert Publisher etc.'''
        print 'start_cm - BEGIN'
        api_url = 'http://%s/api/%s/cm/service/commands/start' % \
                  (self.cm_api_entrypoint, self.cm_api_version)
        cm_cmd = self.rest_util.post(url=api_url)
        cmd_status = self._wait_for_command_finish(cm_cmd['id'])
        if cmd_status:
            print 'start_cm - DONE'
        else:
            raise RuntimeError('start_cm - failed.')

    def deploy_client_config(self, cluster_name=None):
        print 'deploy_client_config - BEGIN'
        api_url = 'http://%s/api/%s/clusters/%s/commands/deployClientConfig' % \
                  (self.cm_api_entrypoint, self.cm_api_version, cluster_name)
        cmd = self.rest_util.post(url=api_url)
        cmd_status = self._wait_for_command_finish(cmd['id'])
        if cmd_status:
            print 'deploy_client_config - DONE'
        else:
            raise RuntimeError('deploy_client_config - failed.')

    def prepare_dir_group_user_ssh(self,
                                   allservers=None,
                                   ssh_user=None,
                                   ssh_pass=None,
                                   ext_ssh_port=2222,
                                   app_superuser=None,
                                   ):
        cmd1 = 'adduser %s;passwd -d %s;groupadd supergroup;usermod -a -G supergroup %s' % \
               (app_superuser,app_superuser,app_superuser)
        for server in allservers:
            print 'connecting to SSH on %s' % server
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(server, port=ext_ssh_port, username=ssh_user, password=ssh_pass)
            print 'executing command %s over SSH to %s' % (cmd1, server)
            stdin, stdout, stderr = client.exec_command(cmd1)
            print 'STDOUT = %s' % stdout.readlines()
            print 'STDERR = %s' % stderr.readlines()
            print 'closing SSH connection to %s' % server
            client.close()

    ##################################################
    # cluster operations for kerberos (some of the operations above are reused)
    ##################################################
    def stop_cluster(self, cluster_name=None):
        '''stop all services in cluster'''
        print 'stop_cluster - BEGIN'
        api_url = 'http://%s/api/%s/clusters/%s/commands/stop' % (self.cm_api_entrypoint, self.cm_api_version, cluster_name)
        cmd = self.rest_util.post(url=api_url)
        cmd_status = self._wait_for_command_finish(cmd['id'])
        if cmd_status:
            print 'stop_cluster - DONE'
        else:
            raise RuntimeError('stop_cluster - failed.')

    def stop_cm(self):
        '''stop the Cloudera Management Services'''
        print 'stop_cm - BEGIN'
        api_url = 'http://%s/api/%s/cm/service/commands/stop' % (self.cm_api_entrypoint, self.cm_api_version)
        cm_cmd = self.rest_util.post(url=api_url)
        cmd_status = self._wait_for_command_finish(cm_cmd['id'])
        if cmd_status:
            print 'stop_cm - DONE'
        else:
            raise RuntimeError('stop_cm - failed.')

    def import_kerberos_admin_credentials(self, kadmin_username=None, kadmin_password=None):
        print 'import_kerberos_admin_credentials - BEGIN'
        api_url = 'http://%s/api/%s/cm/commands/importAdminCredentials?username=%s&password=%s' \
                  % (self.cm_api_entrypoint, self.cm_api_version, kadmin_username, kadmin_password)
        cmd = self.rest_util.post(url=api_url)
        cmd_status = self._wait_for_command_finish(cmd['id'])
        if cmd_status:
            print 'import_kerberos_admin_credentials - DONE'
        else:
            raise RuntimeError('import_kerberos_admin_credentials - failed.')

    def deploy_kerberos_client_config(self, cluster_name=None):
        '''
        Deploy the Cluster's Kerberos client configuration.
        Deploy krb5.conf to hosts in a cluster.
        Does not deploy to decommissioned hosts or hosts with active processes.
        '''
        print 'deploy_kerberos_client_config - BEGIN'
        api_url = 'http://%s/api/%s/clusters/%s/commands/deployClusterClientConfig' % \
                  (self.cm_api_entrypoint, self.cm_api_version, cluster_name)
        cmd = self.rest_util.post(url=api_url)
        cmd_status = self._wait_for_command_finish(cmd['id'])
        if cmd_status:
            print 'deploy_kerberos_client_config - DONE'
        else:
            raise RuntimeError('deploy_kerberos_client_config - failed')

    def configure_cluster_for_kerberos(self, cluster_name=None):
        '''
        Command to configure the cluster to use Kerberos for authentication.
        This command will configure all relevant services on a cluster for Kerberos usage.
        This command will trigger a GenerateCredentials command to create Kerberos keytabs for all roles in the cluster.
        '''
        print 'configure_cluster_for_kerberos - BEGIN'
        api_url = 'http://%s/api/%s/clusters/%s/commands/configureForKerberos' % \
                  (self.cm_api_entrypoint, self.cm_api_version, cluster_name)
        cmd = self.rest_util.post(url=api_url)
        cmd_status = self._wait_for_command_finish(cmd['id'])
        if cmd_status:
            print 'configure_cluster_for_kerberos - DONE'
        else:
            raise RuntimeError('configure_cluster_for_kerberos - failed.')

    def start_cluster(self, cluster_name=None):
        '''start all services in cluster'''
        print 'start_cluster - BEGIN'
        api_url = 'http://%s/api/%s/clusters/%s/commands/start' % \
                  (self.cm_api_entrypoint, self.cm_api_version, cluster_name)
        cmd = self.rest_util.post(url=api_url)
        cmd_status = self._wait_for_command_finish(cmd['id'])
        if cmd_status:
            print 'start_cluster - DONE'
        else:
            raise RuntimeError('start_cluster - failed.')

if __name__ == '__main__':

    # step number to its name (as well as method name)
    steps = {
        '1' : 'create_cluster',
        '2' : 'install_all_hosts',
        '3' : 'add_hosts_to_cluster',
        '4' : 'distribute_parcel_on_cluster',
        '5' : 'activate_parcel_on_cluster',
        '6' : 'upload_cluster_config',
        '7' : 'import_kerberos_admin_credentials',
        '8' : 'deploy_kerberos_client_config',
        '9' : 'configure_cluster_for_kerberos',
        '10': 'start_cm',
        '11': 'firstrun_cluster',
        '12': 'prepare_dir_group_user_ssh',
        '13': 'deploy_client_config',
    }

    parser = optparse.OptionParser(usage="Usage : %prog [options]")
    parser.add_option('--cm_user', type=str, help='cm admin username')
    parser.add_option('--cm_pass', type=str, help='cm admin Password')
    parser.add_option('--cm_api_entrypoint', type=str, help='cm api entrypoint, such as "cmc1.net1:7180"')
    parser.add_option('--cluster_name', type=str, help='cm hadoop cluster name, such as "Cluster1"')
    parser.add_option('--cm_api_version', type=str, help='cm api version, such as "v12"')
    parser.add_option('--cmserver', type=str, help='cm server hostname, such as "cmc1.net1"')
    parser.add_option('--cmagents', type=str, help='cm agents hostnames, such as "cmc2.net,cmc3.net1"')
    parser.add_option('--ssh_user', type=str, help='ssh username of cm agent, for cm server to perform installation')
    parser.add_option('--ssh_pass', type=str, help='ssh password of cm agent, for cm server to perform installation')
    parser.add_option('--ext_ssh_port', type=str, help='ssh port on cm server or agents accessible from this client, such as "2222"')
    parser.add_option('--cdh_parcel', type=str, help='name of the cdh parcel, such as "5.7.1-1.cdh5.7.1.p0.11"')
    parser.add_option('--cdh_version', type=str, help='cdh version, such as "CDH5"')
    parser.add_option('--cdh_full_version', type=str, help='cdh full version, such as "5.7.1"')
    parser.add_option('--cm_repo_url', type=str, help='cdh cm repo url, such as "http://archive.cloudera.com/cm5/redhat/7/x86_64/cm/5.7.1"')
    parser.add_option('--gpg_key_custom_url', type=str, help='cdh cmd gpg key custom url, such as "http://archive.cloudera.com/cm5/redhat/7/x86_64/cm/RPM-GPG-KEY-cloudera"')
    parser.add_option('--config_file_location', type=str, help='Parameterized cluster config file location')
    parser.add_option('--substitution_file_location', type=str, help='Substitution file location')
    parser.add_option('--app_superuser', type=str, help='Specify a single superuser used by client')
    parser.add_option('--steps', type=str, help='run a specific step or ranges of steps, available steps are: %s' %
                                                      reduce(lambda s1, s2: '{}\n{}'.format(s1, s2),
                                                             OrderedDict(
                                                                     sorted(steps.items(), key=lambda t: int(t[0]))
                                                             ).items())
                      )
    # below are kerberos related configs
    parser.add_option('--authnz', type=str, help='authentication mode, value is "simple" or "kerberos"')
    parser.add_option('--kdc_host', type=str, help='kerberos kdc host')
    # do not need krb realm here, it is specified in the substitution file
    #parser.add_option('--security_realm', type=str, help='kerberos security realm')
    parser.add_option('--kadmin_username', type=str, help='kdc admin username, suffixed by realm')
    parser.add_option('--kadmin_password', type=str, help='kdc admin password')

    opts, args = parser.parse_args()

    ##################################################
    # input validation and completion
    ##################################################
    if not opts.cm_user or \
            not opts.cm_pass or\
            not opts.cm_api_entrypoint or \
            not opts.cluster_name or\
            not opts.cm_api_version or \
            not opts.cmserver or \
            not opts.cmagents or \
            not opts.ssh_user or \
            not opts.ssh_pass or \
            not opts.ext_ssh_port or \
            not opts.cdh_parcel or \
            not opts.cdh_version or \
            not opts.cdh_full_version or \
            not opts.cm_repo_url or \
            not opts.gpg_key_custom_url or \
            not opts.app_superuser:
        parser.print_help()
        sys.exit(1)

    if not opts.config_file_location:
        parser.print_help()
        sys.exit(1)

    if not opts.substitution_file_location:
        opts.substitution_file_location = './substitution.json'

    # sanity-check kerberos configs, in case they are set
    if not opts.authnz or opts.authnz == 'simple':
        pass
    elif opts.authnz == 'kerberos':
        if not opts.kdc_host or \
            not opts.kadmin_username or \
            not opts.kadmin_password:
            parser.print_help()
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

    ns = None
    if opts.steps:
        ns = segment.NumericSegment(opts.steps)

    splitted_cmagents= opts.cmagents.split(',')

    # deployer to perform cluster deployment
    cm_cluster_deployer = CMClusterDeployer(
        cm_user=opts.cm_user,
        cm_pass=opts.cm_pass,
        cm_api_entrypoint=opts.cm_api_entrypoint,
        cm_api_version=opts.cm_api_version
    )

    ##################################################
    # 1. create the cluster if it does not exist
    ##################################################
    if not ns or ns.contains(1):
        cm_cluster_deployer.create_cluster(cluster_name=opts.cluster_name,
                                           cdh_version=opts.cdh_version,
                                           cdh_full_version=opts.cdh_full_version)
        if ns and ns.below(1):
            sys.exit(0)

    ##################################################
    # 2. install on agent hosts
    ##################################################
    if not ns or ns.contains(2):
        cm_cluster_deployer.install_all_hosts(cmserver=opts.cmserver,
                                              cmagents=splitted_cmagents,
                                              ssh_user=opts.ssh_user,
                                              ssh_pass=opts.ssh_pass,
                                              ssh_port=22,
                                              cmRepoUrl=opts.cm_repo_url,
                                              gpgKeyCustomUrl=opts.gpg_key_custom_url)
        if ns and ns.below(2):
            sys.exit(0)

    # after installation of hosts (cmserver, cmagents) by names, their ids are assigned,
    # now we can gather their name to [id, ip] mappings
    all_hosts_info = cm_cluster_deployer.get_all_host_info()
    print 'all_hosts_info = %s' % all_hosts_info
    all_host_ids = [all_hosts_info[hkey][0] for hkey in all_hosts_info.keys()]
    print 'agent_host_ids = %s' % all_host_ids

    ##################################################
    # 3. add hosts to cluster
    ##################################################
    if not ns or ns.contains(3):
        cm_cluster_deployer.add_hosts_to_cluster(cluster_name=opts.cluster_name,
                                                 host_ids=all_host_ids)
        if ns and ns.below(3):
            sys.exit(0)


    ##################################################
    # 4. distribute parcels on the cluster
    ##################################################
    if not ns or ns.contains(4):
        cm_cluster_deployer.distribute_parcel_on_cluster(cluster_name=opts.cluster_name,
                                                         cdh_parcel=opts.cdh_parcel)
        if ns and ns.below(4):
            sys.exit(0)

    ##################################################
    # 5. activate parcels on the cluster
    ##################################################
    if not ns or ns.contains(5):
        cm_cluster_deployer.activate_parcel_on_cluster(cluster_name=opts.cluster_name,
                                                       cdh_parcel=opts.cdh_parcel)
        if ns and ns.below(5):
            sys.exit(0)

    ##################################################
    # 6. upload the cluster config to cm
    ##################################################
    # this is a workaround to prepare substitution variables only available
    # after partially created the cluster, as such, they can not be specified
    # statically in the substitution file
    # TODO make this generic probably in the substitution file as scripts
    substitution_runtime={}
    substitution_runtime['REPLACE_CMSERVER_ID'] = all_hosts_info[opts.cmserver][0]
    substitution_runtime['REPLACE_CMSERVER_IP'] = all_hosts_info[opts.cmserver][1]
    if len(splitted_cmagents) >= 1:
        substitution_runtime['REPLACE_CMAGENT_ID1'] = all_hosts_info[splitted_cmagents[0]][0]
        substitution_runtime['REPLACE_CMAGENT_IP1'] = all_hosts_info[splitted_cmagents[0]][1]
    if len(splitted_cmagents) >= 2:
        substitution_runtime['REPLACE_CMAGENT_ID2'] = all_hosts_info[splitted_cmagents[1]][0]
        substitution_runtime['REPLACE_CMAGENT_IP2'] = all_hosts_info[splitted_cmagents[1]][1]

    # cmconfig to load, merge and materialize the parameterized configs
    cm_config = cmconfig.CMConfig()
    clusterjsoncfg = None
    while not clusterjsoncfg or clusterjsoncfg == 'null':
        time.sleep(2)
        clusterjsoncfg = cm_config.materialize_config(opts.config_file_location,
                                                      opts.substitution_file_location,
                                                      substitution_runtime)

    # upload cluster config
    if not ns or ns.contains(6):
        print 'FINAL CLUSTER CONFIG = \n%s ' % json.dumps(clusterjsoncfg, indent=4, sort_keys=True)
        cm_cluster_deployer.upload_cluster_config(json_config=clusterjsoncfg)
        if ns and ns.below(6):
            sys.exit(0)

    ##################################################
    # 7. import kdc admin credentials
    ##################################################
    if opts.authnz == 'kerberos':
        if not ns or ns.contains(7):
            cm_cluster_deployer.import_kerberos_admin_credentials(
                kadmin_username=opts.kadmin_username, kadmin_password=opts.kadmin_password)
            if ns and ns.below(7):
                sys.exit(0)

    ##################################################
    # 8. deploy kerberos client config
    ##################################################
    if opts.authnz == 'kerberos':
        if not ns or ns.contains(8):
            cm_cluster_deployer.deploy_kerberos_client_config(cluster_name=opts.cluster_name)
            if ns and ns.below(8):
                sys.exit(0)

    ##################################################
    # 9. configure cluster for kerberos mode
    ##################################################
    if opts.authnz == 'kerberos':
        if not ns or ns.contains(9):
            cm_cluster_deployer.configure_cluster_for_kerberos(cluster_name=opts.cluster_name)
            if ns and ns.below(9):
                sys.exit(0)

    ##################################################
    # 10. start cm services
    ##################################################
    if not ns or ns.contains(10):
        # TODO remove this workaround, see https://community.cloudera.com/t5/Cloudera-Manager-Installation/Where-does-Cloudera-Manager-store-generated-keytabs-and/td-p/16314
        print 'sleep for 10 seconds'
        time.sleep(10)
        cm_cluster_deployer.start_cm()
        if ns and ns.below(10):
            sys.exit(0)

    ##################################################
    # 11. first run
    ##################################################
    if not ns or ns.contains(11):
        cm_cluster_deployer.firstrun_cluster(cluster_name=opts.cluster_name)
        if ns and ns.below(11):
            sys.exit(0)

    ##################################################
    # 12. setup supergroup, application specific superuser and permissions on hdfs
    ##################################################
    all_hostnames = []
    all_hostnames.append(opts.cmserver)
    for cmagent in splitted_cmagents:
        all_hostnames.append(cmagent)

    if not ns or ns.contains(12):
        cm_cluster_deployer.prepare_dir_group_user_ssh(allservers=all_hostnames,
                                                       ssh_user=opts.ssh_user,
                                                       ssh_pass=opts.ssh_pass,
                                                       ext_ssh_port=int(opts.ext_ssh_port),
                                                       app_superuser=opts.app_superuser)
        if ns and ns.below(12):
            sys.exit(0)

    ##################################################
    # 13. deploy client config
    ##################################################
    if not ns or ns.contains(13):
        cm_cluster_deployer.deploy_client_config(cluster_name=opts.cluster_name)
        if ns and ns.below(13):
            sys.exit(0)

    print 'DEPLOY DONE.'

