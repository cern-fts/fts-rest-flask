#!/bin/sh
set -e

# -------------------------------------------------------------------
# Utility script to help packaging the fts-rest-server.
# The script must be called from the packaging directory
# and expects an rpmdev tree already exists
# -------------------------------------------------------------------

function print_info {
  printf "======================\n"
  printf "Branch:\t\t%s\n" "${BRANCH}"
  printf "Release:\t%s\n" "${RELEASE}"
  printf "Version:\t%s\n" "${VERSION}"
  printf "======================\n"
}

# Setup
TMPDIR=$(mktemp -d /tmp/fts-rest-server-build_XXXXX)
VERSION=$(grep -m1 packaging/fts-rest-server.spec -e "^Version:" | awk {'print $2'})
TIMESTAMP=`date +%y%m%d%H%M`
GITREF=`git rev-parse --short HEAD`
RELEASE=r${TIMESTAMP}git${GITREF}
DISTDIR=${TMPDIR}/fts-rest-server-${VERSION}

if [[ -z ${BRANCH} ]]; then
  BRANCH=`git name-rev $GITREF --name-only`
else
  printf "Using environment set variable BRANCH=%s\n" "${BRANCH}"
fi

if [[ $BRANCH =~ ^(tags\/)?(v)[.0-9]+(-(rc)?([0-9]+))?(-(server|client))?$ ]]; then
  RELEASE="${BASH_REMATCH[4]}${BASH_REMATCH[5]}"
fi

if [[ ! -z ${RELEASE} ]]; then
  sed -i "s/Release:.*/Release: ${RELEASE}%{?dist}/g" packaging/fts-rest-server.spec
fi

print_info

mkdir -p ${DISTDIR}/src

# Copying files for dist
cp LICENSE ${DISTDIR}
cp -r src/fts3rest ${DISTDIR}

# Create tarball
tar -C ${TMPDIR} -czf fts-rest-server-${VERSION}.tar.gz fts-rest-server-${VERSION}/

# Copy spec file to rpmbuild
mv fts-rest-server-${VERSION}.tar.gz ~/rpmbuild/SOURCES/
cp packaging/fts-rest-server.spec ~/rpmbuild/SPECS

rm -rf ${TMPDIR}
echo "Created tarball: " ~/rpmbuild/SOURCES/fts-rest-server-${VERSION}.tar.gz

cd ~/rpmbuild/SPECS

rpmbuild -bs fts-rest-server.spec
rpmbuild -bb fts-rest-server.spec