#!/bin/bash

eval $(ai-rc --same-project-as fts-devel-01)

openstack server list  > /dev/null 2>&1
if [ $? != "0" ] ; then
  echo "openstack server not working"
  exit
fi

ENVIRO="qa"
KEYPAIR="fts3ops"
HOSTGROUP="fts/devel/mysql/live/flask"

if [ "$#" -ne 1 ]
then
  echo "host name required"
  exit 1
fi

hostname=$1

ai-bs \
     --foreman-hostgroup "${HOSTGROUP}" \
     --foreman-environment "${ENVIRO}" \
     --landb-mainuser 'FTS-3RD' \
     --landb-responsible 'FTS-3RD' \
     --nova-flavor "m2.large" \
     --nova-sshkey "${KEYPAIR}" \
     --landb-ipv6ready \
     --cc7 \
 $hostname


