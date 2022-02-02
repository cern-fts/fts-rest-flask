#!/bin/sh
set -e

# -------------------------------------------------------------------
# Utility script to help packaging the fts-rest-client.
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
TMPDIR=$(mktemp -d /tmp/fts-rest-client-build_XXXXX)
VERSION=$(grep -m1 packaging/fts-rest-client.spec -e "^Version:" | awk {'print $2'})
TIMESTAMP=`date +%y%m%d%H%M`
GITREF=`git rev-parse --short HEAD`
RELEASE=r${TIMESTAMP}git${GITREF}
DISTDIR=${TMPDIR}/fts-rest-client-${VERSION}

if [[ -z ${BRANCH} ]]; then
  BRANCH=`git name-rev $GITREF --name-only`
else
  printf "Using environment set variable BRANCH=%s\n" "${BRANCH}"
fi

if [[ $BRANCH =~ ^(tags/)?(v)[.0-9]+(-(rc)?([0-9]+))?$ ]]; then
  RELEASE="${BASH_REMATCH[4]}${BASH_REMATCH[5]}"
fi

print_info

mkdir -p ${DISTDIR}/src

# Copying files for dist
cp LICENSE ${DISTDIR}
cp setup.py ${DISTDIR}
cp setup.cfg ${DISTDIR}
cp -r src/cli src/fts3 ${DISTDIR}/src

# Create tarball
tar -C ${TMPDIR} -czf fts-rest-client-${VERSION}.tar.gz fts-rest-client-${VERSION}/

# Place files in
mv fts-rest-client-${VERSION}.tar.gz ~/rpmbuild/SOURCES/
cp packaging/fts-rest-client.spec ~/rpmbuild/SPECS

rm -rf ${TMPDIR}
echo "Created tarball:" ~/rpmbuild/SOURCES/fts-rest-client-${VERSION}.tar.gz

cd ~/rpmbuild/SPECS

rpmbuild -bs --define "_release ${RELEASE}" fts-rest-client.spec
rpmbuild -bb --define "_release ${RELEASE}" fts-rest-client.spec