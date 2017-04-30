#!/usr/bin/env bash

CM_ADMIN_USERNAME=admin
CM_ADMIN_PASSWORD=admin
CM_CLUSTER_NAME=Cluster1
CM_API_VERSION=12
CM_HOSTNAME="$(hostname -f)"
API_CLUSTER_BASE="http://$CM_HOSTNAME:7180/api/v$CM_API_VERSION/clusters/$CM_CLUSTER_NAME"
API_CM_BASE="http://$CM_HOSTNAME:7180/api/v$CM_API_VERSION/cm"
API_COMMANDS_BASE="http://$CM_HOSTNAME:7180/api/v$CM_API_VERSION/commands"

INITIAL_START_DONE_FLAG="/var/lib/.cloudera-manager"

function log()
{
    echo "[$(date +"%T")][DEPLOYER] ${1}"
}

function wait_for_command_done()
{
    local CMD_ID="$@"
    local CHECK_CMD="curl -sS -u "$CM_ADMIN_USERNAME:$CM_ADMIN_PASSWORD" "$API_COMMANDS_BASE/$CMD_ID" | jq '.success'"

    while [[ "$(eval $CHECK_CMD)" == "null" ]]
    do
        log "Waiting for done of command=$CMD_ID"
        sleep 10
    done

    if [[ "$(eval $CHECK_CMD)" == "true" ]]
    then
        log "command=$CMD_ID is done"
    else
        log "command=$CMD_ID failed"
        exit 1
    fi
}

function waitcm()
{
    # TODO - a short cut check only on port 7180 for service 'cloudera-scm-server'
    local isOpen=$(nmap -sT $CM_HOSTNAME -p 7180 | grep open)
    while [[ -z "$isOpen" ]]
    do
      log "Waiting for CM to be started on port 7180"
      sleep 5
      isOpen=$(nmap -sT $CM_HOSTNAME -p 7180 | grep open)
    done
    log "waitcm - DONE"
}

function startcm()
{
    # the cm core agents, this list is for the server, not for agent
    cloudera-scm-server-db start
    cloudera-scm-server start
    #cloudera-scm-agent start
}

function stopcm()
{
    # the cm core agents, this list is for the server, not for agent
    #cloudera-scm-agent stop
    cloudera-scm-server stop
    cloudera-scm-server-db stop
}

function restart_cm_services()
{
    # TODO - the management services may not exists
    # the cm core services
    log "restarting cm services..."
    local command="curl -sS -u $CM_ADMIN_USERNAME:$CM_ADMIN_PASSWORD -X POST $API_CM_BASE/service/commands/restart | jq '.id'"
    log "command=$command"
    local CMD_ID=$(command)
    wait_for_command_done $CMD_ID
    log "restarting cm services done"
}

function restart_cluster_services()
{
    # TODO - the cluster services may not exists
    # services of the cluster, this also redeploy client configs
    log "restarting cluster services for cluster $CM_CLUSTER ..."
    CMD_ID=$(curl -sS -u "$CM_ADMIN_USERNAME:$CM_ADMIN_PASSWORD" -X POST -H "Content-Type:application/json" -d '{ "redeployClientConfiguration": "true" }' "$API_CLUSTER_BASE/commands/restart" | jq '.id')
    wait_for_command_done $CMD_ID
    log "restarting cluster services for cluster $CM_CLUSTER done"
}

function main()
{
    if [[ ! -e $INITIAL_START_DONE_FLAG ]]; then
        log "initial start of cm..."
        startcm
        waitcm
        touch $INITIAL_START_DONE_FLAG
    else
        log "restart of cm..."
        stopcm
        startcm
        waitcm
        restart_cm_services
        restart_cluster_services
    fi
}

main "$@"
