#!/bin/bash

export OS_IDENTITY_API_VERSION=3
export OS_PROJECT_DOMAIN_ID=default
export OS_PROJECT_NAME="IT FTS development"
export OS_AUTH_URL=https://keystone.cern.ch/v3
export OS_USERNAME=$USER

openstack server list  > /dev/null 2>&1
if [ $? != "0" ] ; then
  echo "openstack server not working"
  exit
fi

export ENVIRO="ftsclean"

KEYPAIR="fts3ops"

if [ "$#" -ne 1 ]
then
  echo "host name required"
  exit 1
fi

hostname=$1

ai-bs \
     --foreman-hostgroup 'fts/devel/flask' \
     --foreman-environment "${ENVIRO}" \
     --landb-mainuser 'FTS-3RD' \
     --landb-responsible 'FTS-3RD' \
     --nova-flavor "m2.large" \
     --nova-sshkey "${KEYPAIR}" \
     --landb-ipv6ready \
     --cc7 \
 $hostname
 

