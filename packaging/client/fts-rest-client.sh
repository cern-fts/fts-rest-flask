#!/bin/sh
set -e

# -------------------------------------------------------------------
# Utility script to build the fts-rest-client RPM.
# Execute the script from the root of the git repository
# -------------------------------------------------------------------

# Build SRPM
rm -rf build/client/
./packaging/client/make-srpm.sh

# Install build dependencies
cd build/client/

if [[ -f /usr/bin/dnf ]]; then
  dnf builddep -y SRPMS/*
else
  yum-builddep -y SRPMS/*
fi

rpmbuild --rebuild SRPMS/* --define "_topdir ${PWD}"
