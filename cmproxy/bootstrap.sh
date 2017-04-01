#!/usr/bin/env bash

if [[ -z "$PROXIED_SERVER" ]]; then
    echo "parameter PROXIED_SERVER is missing."
    exit 1
fi

echo "parameter PROXIED_SERVER=$PROXIED_SERVER"

if [[ -z "$OVERLAY_NET" ]]; then
    echo "parameter OVERLAY_NET is missing."
    exit 1
fi

echo "parameter OVERLAY_NET=$OVERLAY_NET"

sed -i "s/PROXIED_SERVER/$PROXIED_SERVER/g" /config/nginx.conf
sed -i "s/OVERLAY_NET/$OVERLAY_NET/g" /config/nginx.conf

nginx

#
#while true; do sleep 1000; done
