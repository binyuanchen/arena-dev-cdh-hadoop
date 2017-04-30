#!/usr/bin/env bash

if [[ -z "$PROXIED_SERVER" ]]; then
    echo "parameter PROXIED_SERVER is missing."
    exit 1
fi

echo "parameter PROXIED_SERVER=$PROXIED_SERVER"
echo "parameter OVERLAY_NET=$OVERLAY_NET"

if [[ -z "$OVERLAY_NET" ]]; then
    sed -i "s/PROXIED_SERVER\.OVERLAY_NET//g" /config/nginx.conf
else
    sed -i "s/PROXIED_SERVER\.OVERLAY_NET/$PROXIED_SERVER\.$OVERLAY_NET/g" /config/nginx.conf    
fi
sed -i "s/PROXIED_SERVER/$PROXIED_SERVER/g" /config/nginx.conf

nginx

#
#while true; do sleep 1000; done
