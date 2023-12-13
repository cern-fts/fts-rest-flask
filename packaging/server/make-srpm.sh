#!/bin/sh
set -e

# -------------------------------------------------------------------
# Utility script to generate FTS-REST-Flask server source RPM.
# Execute the script from the root of the git repository
# -------------------------------------------------------------------

function print_info {
  printf "======================\n"
  printf "Branch:\t\t%s\n" "${BRANCH}"
  printf "Release:\t%s\n" "${RELEASE}"
  printf "Version:\t%s\n" "${VERSION}"
  printf "======================\n"
}

VERSION=$(grep -m1 packaging/server/fts-rest-server.spec -e "^Version:" | awk {'print $2'})
TIMESTAMP=$(git log -1 --format="%at" | xargs -I{} date -d @{} +%y%m%d%H%M)
GITREF=`git rev-parse --short HEAD`
RELEASE=r${TIMESTAMP}git${GITREF}

if [[ -z ${BRANCH} ]]; then
  BRANCH=`git name-rev $GITREF --name-only`
else
  printf "Using environment set variable BRANCH=%s\n" "${BRANCH}"
fi

if [[ $BRANCH =~ ^(tags\/)?(v)[.0-9]+(-(rc)?([0-9]+))?(-(server|client))?$ ]]; then
  RELEASE="${BASH_REMATCH[4]}${BASH_REMATCH[5]}"
fi

if [[ ! -z ${RELEASE} ]]; then
  sed -i "s/Release:.*/Release: ${RELEASE}%{?dist}/g" packaging/server/fts-rest-server.spec
fi

print_info

# Generate tarball
./packaging/server/make-dist.sh

# Generate SRPM
SPECFILE="${PWD}/packaging/server/fts-rest-server.spec"
pushd build/server/
rpmbuild -bs "${SPECFILE}" --define "_topdir ${PWD}" --define "_sourcedir ${PWD}"
