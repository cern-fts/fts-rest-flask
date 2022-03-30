#!/bin/bash
set -e

#-----------------------------------------------------------------------
# File: install-httpd-dev.sh
# Description: Install FTS-REST-Flask HTTPd config for Development environment.
# Input: fts3rest_dev.conf.in
# Output: /etc/httpd/conf.d/fts3rest_dev.conf
#-----------------------------------------------------------------------

function usage {
  filename=$(basename $0)
  echo "Install FTS-REST-Flask HTTPd file for Development environment."
  echo "By default, a Python 'venv' directory is expected in the project base directory."
  echo "The script can accept a different 'venv' location as input relative to the project base directory."
  echo ""
  echo "usage: $filename [--venv <venv>]"
  echo "       --venv      -- Python virtual environment path within the project base directory (default = 'venv')"
  echo ""

  exit 1
}

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  usage
fi

VENV="venv"
if [[ "$1" == "--venv" ]]; then
  if [[ -z "$2" ]]; then
    echo "Missing <venv> argument!"
    exit 1
  fi

  VENV="$2"
fi

FILENAME=$(readlink -f "$0")
PROJECT_DIR="${FILENAME%fts-rest-flask*}fts-rest-flask"

cp -f fts3rest_dev.conf.in fts3rest_dev.conf
sed -i "s|%%PROJECT_DIR%%|${PROJECT_DIR}|g" fts3rest_dev.conf
sed -i "s|%%VENV%%|${VENV}|g" fts3rest_dev.conf

mv -fv fts3rest_dev.conf /etc/httpd/conf.d/fts3rest_dev.conf
systemctl restart httpd
