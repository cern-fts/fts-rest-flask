#!/bin/sh
set -e

# -------------------------------------------------------------------
# Utility script to build the fts-rest-server RPM.
# Execute the script from the root of the git repository
# -------------------------------------------------------------------

# Build SRPM
rm -rf build/server/
./packaging/server/make-srpm.sh

# Install build dependencies
cd build/server/
dnf builddep -y SRPMS/*

rpmbuild --rebuild SRPMS/* --define "_topdir ${PWD}"
