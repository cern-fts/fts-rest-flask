#!/bin/bash

#-----------------------------------------------------------------------
# File: pipcompile.sh
# Description: Install FTS-REST-Flask requirements via pip.
#              If enabled, will also sync the environment
#              with the generated package hashes.
# Input: requirements.in dev-requirements.in
# Output: requirements.txt dev-requirements.txt
#-----------------------------------------------------------------------


function usage {
  filename=$(basename $0)
  echo "Install FTS-REST-Flask requirements via pip."
  echo "Note: Make sure to run this within a Python virtual environment"
  echo ""
  echo "usage: $filename [--sync]"
  echo "       --sync      -- Also run 'pip-sync' on the generated hashes"
  echo ""

  exit 1
}

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  usage
fi

run_sync=false
if [[ "$1" == "--sync" ]]; then
  run_sync=true
fi

pip-compile --generate-hashes --upgrade requirements.in
pip-compile --generate-hashes --upgrade dev-requirements.in

if [[ "${run_sync}" = true ]]; then
  pip-sync requirements.txt dev-requirements.txt
fi
